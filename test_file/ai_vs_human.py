import sys
import os
import random
import threading
import queue
import requests
import json
import time
import pygame
import unicodedata
import re

# Add parent directory to path to allow importing db_module when running from test_file/
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from typing import List, Tuple, Optional
from db_module.quiz import get_random_quiz_by_category, list_quiz_titles
from db_module.db_connection import get_connection
from db_module.score import insert_ai_data, exist, update_ai_score, get_ai_data

# --- Configuration ---
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 800
BG_COLOR = (240, 242, 245)
ACCENT_COLOR = (59, 130, 246)  # Blue-500
AI_COLOR = (239, 68, 68)       # Red-500
HUMAN_COLOR = (34, 197, 94)    # Green-500
TEXT_COLOR = (31, 41, 55)
SUBTEXT_COLOR = (107, 114, 128)
BOX_BG = (255, 255, 255)
BOX_BORDER = (229, 231, 235)

TITLE = "AI vs Human Quiz Battle"
AI_MODEL = "gemma3:4b" # Updated to match lamarun.py as requested

# --- States ---
STATE_LOGIN = "LOGIN"
STATE_MENU = "MENU"
STATE_ROULETTE = "ROULETTE"
STATE_COUNTDOWN = "COUNTDOWN"
STATE_GAME = "GAME"
STATE_RESULT = "RESULT"

# --- Utils (Reused/Adapted) ---
def load_korean_font(size: int) -> pygame.font.Font:
    # Try generic or system fonts
    candidates = [
        "Apple SD Gothic Neo", "AppleGothic", # macOS priorities
        "Malgun Gothic", # Windows
        "Noto Sans KR", "NanumGothic", "Gothic", "Arial Unicode MS"
    ]
    for name in candidates:
        try:
            matched = pygame.font.match_font(name)
            if matched:
                return pygame.font.Font(matched, size)
        except:
            continue
    # Fallback
    return pygame.font.SysFont("arial", size)

def normalize_text(text: str) -> str:
    # Fix macOS specific Hangeul decomposition issue
    return unicodedata.normalize('NFC', text)

def wrap_text(text: str, font: pygame.font.Font, max_width: int) -> List[str]:
    text = normalize_text(text)
    lines = []
    if not text: return [""]
    for para in text.split("\n"):
        words = para.split(" ")
        current = ""
        for w in words:
            test = (current + " " + w).strip() if current else w
            if font.size(test)[0] <= max_width:
                current = test
            else:
                if current: lines.append(current)
                current = w
        if current: lines.append(current)
    return lines

def draw_rect_with_border(screen, rect, bg_color, border_color=None, width=0, radius=8):
    pygame.draw.rect(screen, bg_color, rect, border_radius=radius)
    if border_color:
        pygame.draw.rect(screen, border_color, rect, 2, border_radius=radius)

def format_time(ms: int) -> str:
    total_sec = ms // 1000
    mins = total_sec // 60
    secs = total_sec % 60
    centis = (ms % 1000) // 10
    return f"{mins:02d}:{secs:02d}.{centis:02d}"

# --- Game Class ---
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()

        # Fonts
        self.fonts = {
            'sm': load_korean_font(20),
            'md': load_korean_font(28),
            'lg': load_korean_font(40),
            'xl': load_korean_font(60), # Reduced slightly
            'xxl': load_korean_font(80)
        }

        # Data
        self.state = STATE_LOGIN
        self.student_id = ""

        self.current_quiz = None
        self.quiz_lines = []

        # Roulette
        self.roulette_candidates = []
        try:
            # list_quiz_titles helper param order_by is limited.
            # Just fetch and shuffle.
            rows = list_quiz_titles(limit=50)
            self.roulette_candidates = [r['title'] for r in rows]
            random.shuffle(self.roulette_candidates)
        except Exception as e:
            print(f"Error loading quiz titles for roulette: {e}")
            self.roulette_candidates = ["Loading...", "Quizzz...", "AI vs Human"]

        self.roulette_start_tick = 0
        self.roulette_idx = 0

        # Gameplay
        self.user_input = ""
        self.start_ticks = 0
        self.game_end_time = 0 # Initialize to avoid AttributeError

        # AI
        self.ai_current_text = ""
        self.ai_queue = queue.Queue()
        self.ai_stop_event = threading.Event()
        self.ai_finished = False
        self.ai_thread = None # To hold the thread object

        self.winner = None  # 'HUMAN', 'AI', None
        self.fail_reason = "" # 'WRONG', 'TOO_SLOW'

        self.input_active = True

        # Animation
        self.cursor_visible = True
        self.cursor_timer = 0

        # game setting
        self.difficulty = "1"
        self.score = 0
        self.game_over_detail = ""

    def get_new_quiz(self):
        # Deck of Cards System: guarantees no repeats until all are shown
        if not hasattr(self, 'quiz_deck') or not self.quiz_deck:
            try:
                # Fetch all questions (limit 100 for now)
                # Note: list_quiz_titles returns 'correct' column by default in this codebase
                rows = list_quiz_titles(limit=100)
                if not rows:
                     return {
                        'title': '퀴즈 데이터를 찾을 수 없습니다.',
                        'description': 'DB에 문제가 있는 것 같습니다.\n확인해주세요.',
                        'correct': 'error'
                    }
                self.quiz_deck = rows
                random.shuffle(self.quiz_deck)
                print(f"[DEBUG] Loaded {len(self.quiz_deck)} questions into deck.")
            except Exception as e:
                print(f"[Error] Failed to load quiz deck: {e}")
                return {
                        'title': 'Error',
                        'description': str(e),
                        'correct': 'error'
                    }

        return self.quiz_deck.pop()

    def run_ollama_worker(self, prompt: str):
        # Logic from lamarun.py adapted for queue
        url = "http://localhost:11434/api/generate"
        model = AI_MODEL # Use a lighter model to be safe or "llama3" if user prefers. Going with gemma2:2b as it is fast.

        # Construct a persona prompt
        full_prompt = (
            f"You are a quiz contestant. The question is: {prompt}\n"
            f"First, describe your thinking process in detail. Do NOT give the answer immediately.\n"
            f"At the very end, provide the final answer in this format: 'Answer: [Your Answer]'"
        )

        payload = {
            "model": model,
            "prompt": full_prompt,
            "stream": True
        }

        try:
            response = requests.post(url, json=payload, stream=True, timeout=30) # Increased timeout
            # Check if model exists, if not 404
            if response.status_code == 404:
                 self.ai_queue.put(f"[System: Model '{model}' not found. Please pull it.]")
                 self.ai_finished = True
                 return
            elif response.status_code != 200:
                 self.ai_queue.put(f"[System: Ollama API Error: {response.status_code} - {response.text}]")
                 self.ai_finished = True
                 return

            # Use iter_lines for safer line-by-line reading
            for line in response.iter_lines():
                if self.ai_stop_event.is_set():
                    break
                if line:
                    try:
                        decoded_line = line.decode('utf-8')
                        data = json.loads(decoded_line)
                        if "response" in data:
                            token = data["response"]
                            self.ai_queue.put(token)
                            print(token, end="", flush=True) # DEBUG to Console

                            # Requested delay
                            time.sleep(0.1)

                        if data.get("done"):
                            break
                    except Exception as e:
                        print(f"[DEBUG] Error parsing line: {e}")

        except requests.exceptions.ConnectionError:
            err = "\n[Error: Could not connect to Ollama. Is it running?]"
            print(err)
            self.ai_queue.put(err)
        except requests.exceptions.Timeout:
            err = "\n[Error: Ollama request timed out.]"
            print(err)
            self.ai_queue.put(err)
        except Exception as e:
            err = f"\n[Error: {e}]"
            print(err)
            self.ai_queue.put(err)

        self.ai_finished = True

    def start_round(self):
        # self.current_quiz is already set in start_roulette_logic
        title = self.current_quiz.get('title', '')
        desc = self.current_quiz.get('description', '')

        text_to_show = f"[{title}]\n{desc}"
        self.quiz_lines = wrap_text(text_to_show, self.fonts['md'], WINDOW_WIDTH - 100)

        self.user_input = ""
        self.state = STATE_COUNTDOWN
        self.countdown_val = 3
        self.last_count_tick = pygame.time.get_ticks()
        self.game_end_time = 0

        # Reset AI
        self.ai_current_text = ""
        # Clear the queue from previous rounds if any
        while not self.ai_queue.empty():
            try:
                self.ai_queue.get_nowait()
            except queue.Empty:
                break
        self.ai_finished = False
        self.ai_stop_event.clear() # Clear the stop event for the new round
        if self.ai_thread and self.ai_thread.is_alive():
            self.ai_stop_event.set() # Signal previous thread to stop if it's still running
            self.ai_thread.join(timeout=1) # Wait a bit for it to finish

        self.winner = None
        self.fail_reason = ""

        # Start AI PREEMPTIVELY during countdown (3, 2, 1...)
        self.start_ai_worker()

    def start_ai_worker(self):
        # Use title + description for prompt
        q_text = self.current_quiz.get('title', '') + " " + self.current_quiz.get('description', '')
        self.ai_thread = threading.Thread(target=self.run_ollama_worker, args=(q_text,))
        self.ai_thread.daemon = True # Allow main program to exit even if thread is running
        self.ai_thread.start()

    def start_game_timers(self):
        self.start_ticks = pygame.time.get_ticks()

    def check_answer(self, user_ans, real_ans):
        def norm(s): return str(s).strip().lower().replace(" ", "")
        return norm(user_ans) == norm(real_ans)

    def run(self):
        while True:
            dt = self.clock.tick(60)
            self.handle_input()
            self.update(dt)
            self.draw()

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.ai_stop_event.set() # Signal AI thread to stop
                pygame.quit(); sys.exit()

            if event.type == pygame.KEYDOWN:
                if self.state == STATE_LOGIN:
                    if event.key == pygame.K_BACKSPACE:
                        self.student_id = self.student_id[:-1]
                    elif event.key == pygame.K_RETURN and self.student_id.strip():
                        self.state = STATE_MENU
                    else:
                        if event.unicode.isnumeric() or event.unicode.isalnum():
                            self.student_id += event.unicode

                elif self.state == STATE_MENU:
                    if event.key == pygame.K_RETURN:
                        self.start_roulette()

                elif self.state == STATE_ROULETTE:
                    pass # Wait for anim

                elif self.state == STATE_GAME:
                    if event.key == pygame.K_BACKSPACE:
                        self.user_input = self.user_input[:-1]
                    elif event.key == pygame.K_RETURN:
                        # Human Submit
                        self.human_submit()
                    else:
                        # Append unicode directly (normalization usually handled by OS input but we'll normalize on render)
                        self.user_input += event.unicode

                elif self.state == STATE_RESULT:
                    if event.key == pygame.K_RETURN:
                        # Reset to Login for new student ID
                        self.student_id = ""
                        self.state = STATE_LOGIN

    def start_roulette(self):
        self.state = STATE_ROULETTE
        self.start_roulette_logic()

    def start_roulette_logic(self):
        self.current_quiz = self.get_new_quiz()
        self.difficulty = str(self.current_quiz.get('difficulty', '1'))
        self.roulette_start_tick = pygame.time.get_ticks()
        # Shuffle candidates for visual variety
        random.shuffle(self.roulette_candidates)

    def human_submit(self):
        # 1. Check Correctness
        correct_ans = self.current_quiz.get('correct', '') or ""
        self.game_end_time = pygame.time.get_ticks() - self.start_ticks

        # 1번 방식: 60,000ms(1분)에서 걸린 시간을 차감 (최소 0점)
        round_score = max(0, 60000 - self.game_end_time)

        # 기존 점수 가져오기 (누적 방식)
        user_data = get_ai_data(self.student_id)
        if user_data:
            self.score = int(user_data['score']) + round_score
        else:
            self.score = round_score

        if self.check_answer(self.user_input, correct_ans):
            self.end_game('HUMAN', 'CORRECT')
        else:
            self.end_game('AI', 'WRONG_ANSWER')

    def end_game(self, winner, reason):
        if self.state == STATE_RESULT:
            return

        self.winner = winner
        self.fail_reason = reason
        self.state = STATE_RESULT
        self.ai_stop_event.set()

        # Detail message logic
        if winner == 'HUMAN':
            if reason == 'AI_WRONG':
                self.game_over_detail = "AI가 오답을 제출하여 승리하셨습니다!"
                add = True
            else:
                self.game_over_detail = "AI보다 빠르고 정확했습니다!"
                add = True
        else:
            if reason == 'WRONG_ANSWER':
                self.game_over_detail = "오답입니다... 정확도가 중요합니다."
                add = False
            elif reason == 'TOO_SLOW':
                self.game_over_detail = "AI가 먼저 정답을 제출했습니다."
                add = False

        try:
            if add :
                insert_ai_data(self.difficulty, self.student_id, self.score, winner)
        except Exception as e:
            print(f"Error while saving score: {e}")

    def update(self, dt):
        self.cursor_timer += dt
        if self.cursor_timer > 500:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0

        if self.state == STATE_ROULETTE:
            now = pygame.time.get_ticks()
            elapsed = now - self.roulette_start_tick

            # Animation duration: 2.5s total
            # 0-2.0s: Spinning
            # 2.0-2.5s: Show Final Title
            # 2.5s: Go to Countdown

            if elapsed < 2000:
                # Cycle rapidly: Change every 50ms increasing to 200ms
                # Simple math for slowing down
                factor = (elapsed / 2000) # 0 to 1
                delay = 50 + int(200 * factor)
                if now % delay < dt + 10: # Rough trigger
                    self.roulette_idx = (self.roulette_idx + 1) % len(self.roulette_candidates)
            elif elapsed < 3000:
                # Show Real Title
                pass
            else:
                self.start_round()

        elif self.state == STATE_COUNTDOWN:
            now = pygame.time.get_ticks()
            if now - self.last_count_tick >= 1000:
                self.countdown_val -= 1
                self.last_count_tick = now
                if self.countdown_val <= 0:
                    self.state = STATE_GAME
                    self.start_game_timers() # Start game timers and AI thread

        elif self.state == STATE_GAME:
            # Read AI Stream
            try:
                while True:
                    token = self.ai_queue.get_nowait()
                    self.ai_current_text += token
            except queue.Empty:
                pass

            # Check if AI finished and human hasn't submitted
            if self.ai_finished and self.winner is None:
                self.game_end_time = pygame.time.get_ticks() - self.start_ticks

                # 1번 방식 점수 계산
                round_score = max(0, 60000 - self.game_end_time)

                # 기존 점수와 합산
                user_data = get_ai_data(self.student_id)
                if user_data:
                    self.score = int(user_data['score']) + round_score
                else:
                    self.score = round_score

                # Validate AI Answer
                # Parse "Answer: [XYZ]" from the end
                # Regex look for "Answer:" then capture until end or newline
                match = re.search(r"Answer:\s*(.*)", self.ai_current_text, re.IGNORECASE)
                ai_correct = False

                correct_val = self.current_quiz.get('correct', '')

                if match:
                    ai_ans = match.group(1).strip()
                    # Remove trailing punctuation often added by LLM
                    ai_ans = ai_ans.rstrip(".'\"")
                    if self.check_answer(ai_ans, correct_val):
                        ai_correct = True
                    else:
                        print(f"[DEBUG] AI Wrong. AI: '{ai_ans}' vs Real: '{correct_val}'")
                else:
                    print(f"[DEBUG] AI format mismatch. Text: {self.ai_current_text[-50:]}")

                if ai_correct:
                    self.end_game('AI', 'TOO_SLOW')
                else:
                    self.end_game('HUMAN', 'AI_WRONG')

    def draw(self):
        self.screen.fill(BG_COLOR)

        if self.state == STATE_LOGIN:
            self.draw_login()
        elif self.state == STATE_MENU:
            self.draw_menu()
        elif self.state == STATE_ROULETTE:
            self.draw_roulette()
        elif self.state == STATE_COUNTDOWN:
            self.draw_game_interface()
            self.draw_overlay_countdown()
        elif self.state == STATE_GAME:
            self.draw_game_interface()
        elif self.state == STATE_RESULT:
            self.draw_game_interface() # Keep game visible
            self.draw_overlay_result()

        pygame.display.flip()

    def draw_roulette(self):
        # Draw Background overlay or just clear
        self.screen.fill(BG_COLOR)

        # Header
        h = self.fonts['lg'].render(normalize_text("Random Selection..."), True, SUBTEXT_COLOR)
        self.screen.blit(h, h.get_rect(center=(WINDOW_WIDTH//2, 200)))

        # Box
        box_rect = pygame.Rect(0, 0, 800, 200)
        box_rect.center = (WINDOW_WIDTH//2, WINDOW_HEIGHT//2)
        draw_rect_with_border(self.screen, box_rect, BOX_BG, ACCENT_COLOR, radius=15)

        # Text
        now = pygame.time.get_ticks()
        elapsed = now - self.roulette_start_tick

        text_to_show = ""
        color = TEXT_COLOR

        if elapsed < 2000:
            if self.roulette_candidates:
                text_to_show = self.roulette_candidates[self.roulette_idx]
            else:
                text_to_show = "..."
        else:
            # Show Real Title
            text_to_show = self.current_quiz.get('title', '')
            color = ACCENT_COLOR
            # Flash effect?
            if (elapsed // 100) % 2 == 0:
                draw_rect_with_border(self.screen, box_rect, BOX_BG, (255, 215, 0), width=4, radius=15) # Gold border

        # Render centered
        # might need wrapping if title is long, but for roulette just truncate or small font
        f = self.fonts['xl']
        if len(text_to_show) > 20: f = self.fonts['lg']
        if len(text_to_show) > 40: f = self.fonts['md']

        lines = wrap_text(text_to_show, f, box_rect.width - 40)
        # Just show first line for punchiness in roulette, or center all
        y = box_rect.centery - (len(lines) * f.get_height()) // 2
        for line in lines:
            s = f.render(line, True, color)
            self.screen.blit(s, s.get_rect(center=(box_rect.centerx, y + f.get_height()//2)))
            y += f.get_height()

    def draw_login(self):
        title = self.fonts['lg'].render(normalize_text("학번을 입력해주세요"), True, TEXT_COLOR)
        self.screen.blit(title, title.get_rect(center=(WINDOW_WIDTH//2, 300)))

        box_rect = pygame.Rect((WINDOW_WIDTH - 400)//2, 400, 400, 60)
        draw_rect_with_border(self.screen, box_rect, BOX_BG, ACCENT_COLOR, radius=10)

        txt_s = self.fonts['md'].render(normalize_text(self.student_id + ("|" if self.cursor_visible else "")), True, TEXT_COLOR)
        self.screen.blit(txt_s, (box_rect.x + 20, box_rect.y + 15))

    def draw_menu(self):
        title = self.fonts['xl'].render(normalize_text("AI vs HUMAN"), True, ACCENT_COLOR)
        self.screen.blit(title, title.get_rect(center=(WINDOW_WIDTH//2, 250)))

        sub = self.fonts['md'].render(normalize_text(f"안녕하세요, {self.student_id}님."), True, TEXT_COLOR)
        self.screen.blit(sub, sub.get_rect(center=(WINDOW_WIDTH//2, 350)))

        msg = self.fonts['md'].render(normalize_text("엔터키를 눌러 퀴즈 대결 시작 (Real-time LLM)"), True, SUBTEXT_COLOR)
        self.screen.blit(msg, msg.get_rect(center=(WINDOW_WIDTH//2, 500)))

    def draw_game_interface(self):
        # Header
        pygame.draw.rect(self.screen, (255, 255, 255), (0, 0, WINDOW_WIDTH, 80))
        pygame.draw.line(self.screen, BOX_BORDER, (0, 80), (WINDOW_WIDTH, 80))

        # Timer (Center Top)
        elapsed = 0
        if self.state == STATE_GAME:
            elapsed = pygame.time.get_ticks() - self.start_ticks
        elif self.state == STATE_RESULT:
            elapsed = self.game_end_time

        time_str = format_time(elapsed)
        t_surf = self.fonts['lg'].render(normalize_text(time_str), True, ACCENT_COLOR)
        self.screen.blit(t_surf, t_surf.get_rect(center=(WINDOW_WIDTH//2, 40)))

        p1 = self.fonts['md'].render(normalize_text("HUMAN (YOU)"), True, HUMAN_COLOR)
        self.screen.blit(p1, (50, 25))

        p2 = self.fonts['md'].render(normalize_text(f"AI ({AI_MODEL})"), True, AI_COLOR)
        p2_rect = p2.get_rect(topright=(WINDOW_WIDTH-50, 25))
        self.screen.blit(p2, p2_rect)

        # Question Area
        q_rect = pygame.Rect(100, 120, WINDOW_WIDTH-200, 300)
        draw_rect_with_border(self.screen, q_rect, BOX_BG, BOX_BORDER)

        y_off = 150
        for line in self.quiz_lines:
            surf = self.fonts['md'].render(line, True, TEXT_COLOR) # quiz_lines already wrapped/normalized
            self.screen.blit(surf, (140, y_off))
            y_off += 40

        # --- SPLIT UI ---
        # Human Area (Bottom Left)
        h_area = pygame.Rect(50, 450, WINDOW_WIDTH//2 - 60, 300)
        draw_rect_with_border(self.screen, h_area, (244, 253, 244), HUMAN_COLOR) # Light green bg

        lbl = self.fonts['sm'].render(normalize_text("당신의 답안"), True, HUMAN_COLOR)
        self.screen.blit(lbl, (h_area.x + 20, h_area.y + 20))

        # Human Input Box
        inp_rect = pygame.Rect(h_area.x + 20, h_area.y + 60, h_area.width - 40, 60)
        draw_rect_with_border(self.screen, inp_rect, (255, 255, 255), HUMAN_COLOR)

        if self.state == STATE_GAME or self.state == STATE_RESULT:
            itxt = self.fonts['md'].render(normalize_text(self.user_input + ("|" if (self.cursor_visible and self.state == STATE_GAME) else "")), True, TEXT_COLOR)
            self.screen.blit(itxt, (inp_rect.x + 15, inp_rect.y + 15))

        # AI Area (Bottom Right)
        a_area = pygame.Rect(WINDOW_WIDTH//2 + 10, 450, WINDOW_WIDTH//2 - 60, 300)
        draw_rect_with_border(self.screen, a_area, (254, 242, 242), AI_COLOR) # Light red bg

        lbl_ai = self.fonts['sm'].render(normalize_text("AI의 답변 스트림"), True, AI_COLOR)
        self.screen.blit(lbl_ai, (a_area.x + 20, a_area.y + 20))

        # AI Logic Output Area (Multi-line)
        ai_box_rect = pygame.Rect(a_area.x + 20, a_area.y + 60, a_area.width - 40, 200)
        draw_rect_with_border(self.screen, ai_box_rect, (255, 255, 255), AI_COLOR)

        if self.state in [STATE_GAME, STATE_RESULT]:
            # Wrap AI text
            ai_lines = wrap_text(self.ai_current_text, self.fonts['sm'], ai_box_rect.width - 20)
            # Show last few lines if too long
            max_lines = 8
            visible_lines = ai_lines[-max_lines:]

            ay = ai_box_rect.y + 10
            for line in visible_lines:
                lsurf = self.fonts['sm'].render(line, True, TEXT_COLOR) # wrap_text handles norm
                self.screen.blit(lsurf, (ai_box_rect.x + 10, ay))
                ay += 25

    def draw_overlay_countdown(self):
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0,0,0,100))
        self.screen.blit(overlay, (0,0))

        cd = self.fonts['xl'].render(normalize_text(str(self.countdown_val)), True, (255, 255, 255))
        self.screen.blit(cd, cd.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2)))


    def draw_overlay_result(self):
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0,0,0,150))
        self.screen.blit(overlay, (0,0))

        box = pygame.Rect(0, 0, 600, 400)
        box.center = (WINDOW_WIDTH//2, WINDOW_HEIGHT//2)
        pygame.draw.rect(self.screen, (255, 255, 255), box, border_radius=20)

        res_txt = normalize_text("패배...")
        res_col = AI_COLOR

        if self.winner == 'HUMAN':
            res_txt = normalize_text("승리! (Human Win)")
            res_col = HUMAN_COLOR

        head = self.fonts['xl'].render(res_txt, True, res_col)
        self.screen.blit(head, head.get_rect(center=(box.centerx, box.y + 80)))

        # Detail
        detail = self.game_over_detail


        det_surf = self.fonts['md'].render(normalize_text(detail), True, TEXT_COLOR)
        self.screen.blit(det_surf, det_surf.get_rect(center=(box.centerx, box.y + 160)))

        # Continue
        cont = self.fonts['sm'].render(normalize_text("엔터키를 눌러 새 게임 시작 (학번 입력)"), True, SUBTEXT_COLOR)
        self.screen.blit(cont, cont.get_rect(center=(box.centerx, box.bottom - 50)))


if __name__ == "__main__":
        Game().run()
