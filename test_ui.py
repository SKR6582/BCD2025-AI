import pygame
import sys
import os
from typing import List, Tuple

# Window and style
WINDOW_WIDTH = 900
WINDOW_HEIGHT = 900
BG_COLOR = (245, 246, 250)
BTN_COLOR = (76, 175, 80)
BTN_HOVER = (69, 160, 73)
BTN_TEXT = (255, 255, 255)
TEXT_COLOR = (40, 40, 40)
SUBTEXT_COLOR = (90, 90, 90)
ACCENT_COLOR = (33, 150, 243)  # blue
OK_COLOR = (56, 142, 60)
ERR_COLOR = (211, 47, 47)
BOX_BG = (255, 255, 255)
BOX_BORDER = (210, 214, 220)
TITLE = "Test UI"

# States
STATE_MENU = "MENU"
STATE_COUNTDOWN = "COUNTDOWN"
STATE_QUIZ = "QUIZ"
STATE_RESULT = "RESULT"
STATE_STUDENT_ID = "STUDENT_ID"


def load_korean_font(size: int) -> pygame.font.Font:
    """
    Try to load a font that supports Korean glyphs across platforms.
    Priority:
    1) FONT_PATH env or local path
    2) Common KR system fonts (macOS/Windows/Linux)
    3) Generic fallbacks
    """
    pygame.font.init()

    # 1) Environment override or local file path
    env_path = os.environ.get("FONT_PATH")
    if env_path and os.path.exists(env_path):
        try:
            return pygame.font.Font(env_path, size)
        except Exception as e:
            print(f"[font] Failed to load FONT_PATH '{env_path}':", e)

    # 2) Try to locate a system font that supports Korean
    # Names include English and Korean variants
    candidates = [
        # Popular, broad coverage
        "묘야체", "Noto Sans CJK KR", "Noto Sans KR", "NotoSansCJKkr", "NotoSansKR",
        # Windows
        "묘야체", "Malgun Gothic", "맑은 고딕", "Gulim", "굴림", "Dotum", "돋움", "Batang", "바탕",
        # macOS
        "묘야체", "Apple SD Gothic Neo", "AppleGothic",
        # Linux common
        "묘야체", "NanumGothic", "나눔고딕", "UnDotum", "Baekmuk Gulim",
        # Wide Unicode
        "묘야체", "Arial Unicode MS",
    ]

    for name in candidates:
        try:
            matched = pygame.font.match_font(name, bold=False, italic=False)
            if matched:
                return pygame.font.Font(matched, size)
        except Exception:
            continue

    # 3) Last resort: default font; may not render KR correctly
    print("[font] Warning: No Korean-capable font found. Text may appear as squares.\n"
          "- You can set FONT_PATH to a .ttf/.otf that supports Korean (e.g., NotoSansKR-Regular.ttf).\n"
          "- Or install a KR font: Windows=맑은 고딕, macOS=Apple SD Gothic Neo, Linux=NanumGothic/Noto Sans KR.")
    return pygame.font.SysFont(None, size)


def draw_button(screen, rect, text, font, hover=False, enabled=True):
    color = BTN_HOVER if hover and enabled else BTN_COLOR
    if not enabled:
        color = (170, 170, 170)
    pygame.draw.rect(screen, color, rect, border_radius=10)
    label = font.render(text, True, BTN_TEXT)
    label_rect = label.get_rect(center=rect.center)
    screen.blit(label, label_rect)


def wrap_text(text: str, font: pygame.font.Font, max_width: int) -> List[str]:
    # Simple word wrap (supports Korean due to spaces; long words will be split by character)
    lines: List[str] = []
    if not text:
        return [""]
    paragraphs = text.split("\n")
    for para in paragraphs:
        words = list(para)
        # Try to split by words first (spaces). If spaces exist, use word-based wrap; else char-based
        if " " in para:
            words = para.split(" ")
            current = ""
            for w in words:
                test = (current + (" " if current else "") + w) if current else w
                if font.size(test)[0] <= max_width:
                    current = test
                else:
                    if current:
                        lines.append(current)
                    # If single word is too wide, hard-wrap by characters
                    if font.size(w)[0] > max_width:
                        fragment = ""
                        for ch in w:
                            if font.size(fragment + ch)[0] <= max_width:
                                fragment += ch
                            else:
                                if fragment:
                                    lines.append(fragment)
                                fragment = ch
                        if fragment:
                            current = fragment
                        else:
                            current = ""
                    else:
                        current = w
            if current:
                lines.append(current)
        else:
            current = ""
            for ch in para:
                if font.size(current + ch)[0] <= max_width:
                    current += ch
                else:
                    lines.append(current)
                    current = ch
            if current:
                lines.append(current)
    return lines


def render_text_box(
    screen: pygame.Surface,
    rect: pygame.Rect,
    text_lines: List[str],
    font: pygame.font.Font,
    color: Tuple[int, int, int] = TEXT_COLOR,
    scroll: int = 0,
    line_spacing: int = 6,
):
    # Draw box
    pygame.draw.rect(screen, BOX_BG, rect, border_radius=8)
    pygame.draw.rect(screen, BOX_BORDER, rect, 2, border_radius=8)

    # Clip to rect for scrolling
    clip_prev = screen.get_clip()
    screen.set_clip(rect.inflate(-16, -16))

    x = rect.x + 12
    y_start = rect.y + 12 - scroll
    y = y_start
    for line in text_lines:
        surf = font.render(line, True, color)
        screen.blit(surf, (x, y))
        y += surf.get_height() + line_spacing

    screen.set_clip(clip_prev)


def draw_input_box(screen, rect, text, font, placeholder="", focus=False, cursor_visible=True):
    pygame.draw.rect(screen, BOX_BG, rect, border_radius=8)
    pygame.draw.rect(screen, ACCENT_COLOR if focus else BOX_BORDER, rect, 2, border_radius=8)

    padding = 10
    shown = text if text else (placeholder if not focus else "")
    color = TEXT_COLOR if text or focus else (160, 160, 160)
    surf = font.render(shown, True, color)
    screen.blit(surf, (rect.x + padding, rect.y + (rect.height - surf.get_height()) // 2))

    if focus and cursor_visible:
        cx = rect.x + padding + surf.get_width() + 2
        cy = rect.y + 10
        ch = rect.height - 20
        pygame.draw.rect(screen, ACCENT_COLOR, (cx, cy, 2, ch))


def format_elapsed(ms: int) -> str:
    # mm.ss.sc (sc = centiseconds)
    total_centis = ms // 10
    minutes = total_centis // 600
    seconds = (total_centis // 100) % 60
    centis = total_centis % 100
    return f"{minutes:02d}.{seconds:02d}.{centis:02d}"


def main():
    pygame.init()
    try:
        screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    except pygame.error as e:
        print("Pygame display init failed:", e)
        return

    pygame.display.set_caption(TITLE)

    # Fonts
    font_small = load_korean_font(24)
    font = load_korean_font(32)
    font_large = load_korean_font(48)
    font_xl = load_korean_font(96)

    clock = pygame.time.Clock()

    # Layout rects
    top_title_y = 70
    center_w = int(WINDOW_WIDTH * 0.8)
    center_x = (WINDOW_WIDTH - center_w) // 2

    button_rect = pygame.Rect(0, 0, 240, 70)
    button_rect.center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)

    # Text input rects
    answer_rect = pygame.Rect(center_x, 560, center_w, 60)
    student_rect = pygame.Rect(center_x, 560, center_w, 60)

    # Boxes for question and explanation
    question_rect = pygame.Rect(center_x, 180, center_w, 320)
    explain_rect = pygame.Rect(center_x, 180, center_w, 380)

    # Quiz data (placeholder). If you want DB integration, tell me the API.
    quiz_question = (
        "다음 코드가 출력하는 결과는 무엇일까요?\n"
        "\n"
        "for i in range(3):\n"
        "    print(i)\n"
    )
    quiz_answer = "0 1 2"  # 공백 구분 허용
    quiz_explain = (
        "range(3)은 0부터 2까지 반복합니다. 따라서 출력은 줄바꿈 기준으로 0, 1, 2가 됩니다.\n"
        "콘솔에서 한 줄로 보면 '0 1 2' 처럼 보일 수 있으나 실제로는 각 줄에 하나씩 출력됩니다.\n"
        "여기서는 정답 비교를 단순화하여 공백 기준으로 '0 1 2'를 허용합니다.\n\n"
        "- 핵심: range(n)은 0부터 n-1까지.\n"
        "- print는 기본적으로 줄바꿈을 포함합니다.\n"
        "- 파이썬 버전에 상관없이 동일하게 동작합니다.\n"
    )

    # Pre-wrapped text
    q_lines = []
    e_lines = []

    # State data
    state = STATE_MENU
    countdown_value = 3
    countdown_last_tick = 0

    answer_text = ""
    student_id = ""

    timer_start_ms = None
    elapsed_ms = 0
    is_correct = False

    # Scroll
    explain_scroll = 0

    # Cursor blink
    cursor_timer = 0
    cursor_visible = True

    running = True
    while running:
        dt = clock.tick(60)  # ms since last frame
        cursor_timer += dt
        if cursor_timer >= 500:
            cursor_timer = 0
            cursor_visible = not cursor_visible

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)

            # Mouse wheel for scrolling explanation
            if state == STATE_RESULT and event.type == pygame.MOUSEWHEEL:
                explain_scroll = max(0, explain_scroll - event.y * 30)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if state == STATE_MENU:
                    if button_rect.collidepoint(mx, my):
                        state = STATE_COUNTDOWN
                        countdown_value = 3
                        countdown_last_tick = pygame.time.get_ticks()
                        # Prepare question wrapping
                        q_lines = wrap_text(quiz_question, font, question_rect.width - 24)
                        answer_text = ""
                        is_correct = False
                        elapsed_ms = 0
                        timer_start_ms = None
                elif state == STATE_STUDENT_ID:
                    # "다시하기" 버튼
                    again_rect = pygame.Rect(0, 0, 220, 60)
                    again_rect.center = (WINDOW_WIDTH // 2, 660)
                    if again_rect.collidepoint(mx, my):
                        # Reset to menu
                        state = STATE_MENU
                        student_id = ""
                        answer_text = ""
                        explain_scroll = 0

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if state in (STATE_MENU, STATE_RESULT):
                        state = STATE_MENU
                    # Don't allow escape elsewhere to avoid accidental exits

                if state == STATE_QUIZ:
                    if timer_start_ms is None:
                        timer_start_ms = pygame.time.get_ticks()
                    if event.key == pygame.K_RETURN:
                        # Submit answer
                        end_ms = pygame.time.get_ticks()
                        elapsed_ms = end_ms - timer_start_ms if timer_start_ms is not None else 0
                        # Normalize and compare
                        def norm(s: str) -> str:
                            return " ".join(s.strip().lower().split())
                        is_correct = norm(answer_text) == norm(quiz_answer)
                        # Prepare explanation lines and go to result
                        e_lines = wrap_text(quiz_explain, font_small, explain_rect.width - 24)
                        explain_scroll = 0
                        state = STATE_RESULT
                    elif event.key == pygame.K_BACKSPACE:
                        if answer_text:
                            answer_text = answer_text[:-1]
                    elif event.key == pygame.K_TAB:
                        # ignore
                        pass
                    else:
                        if event.unicode:
                            answer_text += event.unicode

                elif state == STATE_STUDENT_ID:
                    if event.key == pygame.K_RETURN:
                        sid = student_id.strip()
                        # Print summary record (can be replaced with DB save)
                        print({
                            'student_id': sid,
                            'correct': is_correct,
                            'elapsed': format_elapsed(elapsed_ms),
                            'answer': answer_text,
                        })
                        # Back to menu
                        state = STATE_MENU
                        student_id = ""
                        answer_text = ""
                    elif event.key == pygame.K_BACKSPACE:
                        if student_id:
                            student_id = student_id[:-1]
                    else:
                        if event.unicode:
                            student_id += event.unicode

        # Update countdown
        if state == STATE_COUNTDOWN:
            now = pygame.time.get_ticks()
            if countdown_last_tick == 0:
                countdown_last_tick = now
            if now - countdown_last_tick >= 1000:
                countdown_last_tick = now
                countdown_value -= 1
                if countdown_value <= 0:
                    # Go to quiz and start timer
                    state = STATE_QUIZ
                    timer_start_ms = pygame.time.get_ticks()

        # Draw
        screen.fill(BG_COLOR)

        # Title
        title_surface = font_large.render("게임: Test UI", True, (60, 60, 60))
        title_rect = title_surface.get_rect(center=(WINDOW_WIDTH // 2, top_title_y))
        screen.blit(title_surface, title_rect)

        if state == STATE_MENU:
            hover = button_rect.collidepoint(pygame.mouse.get_pos())
            draw_button(screen, button_rect, "시작", font, hover=hover)
            tip = font_small.render("시작을 누르면 3,2,1 카운트 후 퀴즈가 시작됩니다.", True, SUBTEXT_COLOR)
            screen.blit(tip, tip.get_rect(center=(WINDOW_WIDTH // 2, button_rect.bottom + 40)))

        elif state == STATE_COUNTDOWN:
            # Dim background
            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 80))
            screen.blit(overlay, (0, 0))

            cd_text = str(countdown_value)
            cd_surf = font_xl.render(cd_text, True, ACCENT_COLOR)
            cd_rect = cd_surf.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
            screen.blit(cd_surf, cd_rect)

        elif state == STATE_QUIZ:
            # Question box
            render_text_box(screen, question_rect, q_lines, font)
            # Answer input
            draw_input_box(
                screen,
                answer_rect,
                answer_text,
                font,
                placeholder="여기에 정답을 입력하고 엔터를 누르세요",
                focus=True,
                cursor_visible=cursor_visible,
            )
            # Timer
            if timer_start_ms is not None:
                elapsed_ms = pygame.time.get_ticks() - timer_start_ms
            t_surf = font_small.render(f"시간: {format_elapsed(elapsed_ms)}", True, SUBTEXT_COLOR)
            screen.blit(t_surf, (answer_rect.x, answer_rect.y - 36))

        elif state == STATE_RESULT:
            # Correctness and time
            result_text = "정답입니다!" if is_correct else "오답입니다"
            result_color = OK_COLOR if is_correct else ERR_COLOR
            r_surf = font_large.render(result_text, True, result_color)
            r_rect = r_surf.get_rect(center=(WINDOW_WIDTH // 2, 120))
            screen.blit(r_surf, r_rect)

            time_surf = font.render(f"걸린 시간: {format_elapsed(elapsed_ms)}", True, TEXT_COLOR)
            screen.blit(time_surf, time_surf.get_rect(center=(WINDOW_WIDTH // 2, 190)))

            # Explanation box (scrollable)
            # Draw scrollbar hint
            hint = font_small.render("스크롤로 해설을 내려보세요", True, SUBTEXT_COLOR)
            screen.blit(hint, hint.get_rect(center=(WINDOW_WIDTH // 2, 155)))

            render_text_box(screen, explain_rect, e_lines, font_small, scroll=explain_scroll)

            # Continue prompt
            cont = font.render("엔터: 학번 입력으로", True, SUBTEXT_COLOR)
            screen.blit(cont, cont.get_rect(center=(WINDOW_WIDTH // 2, 590)))

            # Enter to go to student id
            keys = pygame.key.get_pressed()
            if keys[pygame.K_RETURN]:
                # Debounce by moving state and clearing keyboard state will be naturally handled next frame
                state = STATE_STUDENT_ID

        elif state == STATE_STUDENT_ID:
            # Prompt
            p1 = font.render("학번을 입력하세요", True, TEXT_COLOR)
            screen.blit(p1, p1.get_rect(center=(WINDOW_WIDTH // 2, 140)))

            draw_input_box(
                screen,
                student_rect,
                student_id,
                font,
                placeholder="학번 입력 후 엔터",
                focus=True,
                cursor_visible=cursor_visible,
            )

            # Again button
            again_rect = pygame.Rect(0, 0, 220, 60)
            again_rect.center = (WINDOW_WIDTH // 2, 660)
            hover = again_rect.collidepoint(pygame.mouse.get_pos())
            draw_button(screen, again_rect, "다시하기", font, hover=hover)

            tip = font_small.render("엔터를 누르면 기록이 콘솔에 출력되고 메뉴로 돌아갑니다.", True, SUBTEXT_COLOR)
            screen.blit(tip, tip.get_rect(center=(WINDOW_WIDTH // 2, again_rect.bottom + 30)))

        pygame.display.flip()


if __name__ == "__main__":
    main()
