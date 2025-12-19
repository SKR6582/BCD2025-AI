document.addEventListener('DOMContentLoaded', () => {
  const quizList = document.getElementById('quiz-list');
  const quizModal = document.getElementById('quiz-modal');
  const quizForm = document.getElementById('quiz-form');
  const addBtn = document.getElementById('add-quiz-btn');
  const cancelBtn = document.getElementById('cancel-btn');
  const modalTitle = document.getElementById('modal-title');

  let currentQuizId = null;

  // Fetch and display quizzes
  const fetchQuizzes = async () => {
    try {
      const res = await fetch('/api/quizzes');
      const data = await res.json();

      if (data.length === 0) {
        quizList.innerHTML = '<tr><td colspan="6" class="empty-state">No quizzes found. Add some!</td></tr>';
        return;
      }

      quizList.innerHTML = data.map(quiz => `
                <tr>
                    <td>
                        <span class="difficulty-badge diff-${quiz.difficulty}">
                            ${getDifficultyText(quiz.difficulty)}
                        </span>
                    </td>
                    <td>
                        <div style="font-weight: 600;">${quiz.title}</div>
                        <div style="font-size: 0.875rem; color: var(--text-muted);">${quiz.category || 'No category'}</div>
                    </td>
                    <td>
                        <div style="max-width: 300px; font-size: 0.875rem;">${quiz.description || ''}</div>
                    </td>
                    <td>
                        <code style="background: rgba(0,0,0,0.3); padding: 0.2rem 0.4rem; border-radius: 0.25rem;">${quiz.correct || ''}</code>
                    </td>
                    <td class="actions">
                        <button class="btn btn-secondary btn-sm" onclick="editQuiz(${JSON.stringify(quiz).replace(/"/g, '&quot;')})">Edit</button>
                        <button class="btn btn-danger btn-sm" onclick="deleteQuiz(${quiz.id})">Delete</button>
                    </td>
                </tr>
            `).join('');
    } catch (err) {
      console.error('Failed to fetch quizzes:', err);
    }
  };

  const getDifficultyText = (diff) => {
    const map = { 1: 'Easy', 2: 'Normal', 3: 'Hard' };
    return map[diff] || 'Unknown';
  };

  // Show modal
  addBtn.addEventListener('click', () => {
    currentQuizId = null;
    modalTitle.textContent = 'Add New Quiz';
    quizForm.reset();
    quizModal.style.display = 'flex';
  });

  // Hide modal
  cancelBtn.addEventListener('click', () => {
    quizModal.style.display = 'none';
  });

  // Close modal on outside click
  window.onclick = (event) => {
    if (event.target == quizModal) {
      quizModal.style.display = 'none';
    }
  };

  // Form submit
  quizForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(quizForm);
    const payload = {
      title: formData.get('title'),
      description: formData.get('description'),
      category: formData.get('category'),
      difficulty: parseInt(formData.get('difficulty')),
      correct: formData.get('correct')
    };

    const method = currentQuizId ? 'PUT' : 'POST';
    const url = currentQuizId ? `/api/quizzes/${currentQuizId}` : '/api/quizzes';

    try {
      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const result = await res.json();

      if (res.ok) {
        quizModal.style.display = 'none';
        fetchQuizzes();
      } else {
        alert('Error: ' + result.error);
      }
    } catch (err) {
      console.error('Failed to save quiz:', err);
    }
  });

  // Global edit function
  window.editQuiz = (quiz) => {
    currentQuizId = quiz.id;
    modalTitle.textContent = 'Edit Quiz';

    quizForm.elements['title'].value = quiz.title;
    quizForm.elements['description'].value = quiz.description || '';
    quizForm.elements['category'].value = quiz.category || '';
    quizForm.elements['difficulty'].value = quiz.difficulty;
    quizForm.elements['correct'].value = quiz.correct || '';

    quizModal.style.display = 'flex';
  };

  // Global delete function
  window.deleteQuiz = async (id) => {
    if (!confirm('Are you sure you want to delete this quiz?')) return;

    try {
      const res = await fetch(`/api/quizzes/${id}`, { method: 'DELETE' });
      if (res.ok) {
        fetchQuizzes();
      } else {
        const result = await res.json();
        alert('Error: ' + result.error);
      }
    } catch (err) {
      console.error('Failed to delete quiz:', err);
    }
  };

  fetchQuizzes();
});
