let data = { blocks: [], bonus_blocks: [] };

// Загрузка данных при старте
document.addEventListener('DOMContentLoaded', async () => {
  await loadData();
  renderBlocks();
  
  // Обработчики кнопок
  document.getElementById('add-normal-block').addEventListener('click', () => addBlock('normal'));
  document.getElementById('add-bonus-block').addEventListener('click', () => addBlock('bonus'));
  document.getElementById('save-btn').addEventListener('click', saveData);
});

async function loadData() {
  try {
    const response = await fetch('/api/questions');
    if (response.ok) {
      data = await response.json();
      if (!data.blocks) data.blocks = [];
      if (!data.bonus_blocks) data.bonus_blocks = [];
    }
  } catch (error) {
    console.error('Ошибка загрузки:', error);
  }
}

function renderBlocks() {
  renderNormalBlocks();
  renderBonusBlocks();
}

function renderNormalBlocks() {
  const container = document.getElementById('normal-blocks');
  container.innerHTML = '';
  
  data.blocks.forEach((block, blockIndex) => {
    const blockDiv = createBlockElement(block, blockIndex, 'normal');
    container.appendChild(blockDiv);
  });
}

function renderBonusBlocks() {
  const container = document.getElementById('bonus-blocks');
  container.innerHTML = '';
  
  data.bonus_blocks.forEach((block, blockIndex) => {
    const blockDiv = createBlockElement(block, blockIndex, 'bonus');
    container.appendChild(blockDiv);
  });
}

function createBlockElement(block, blockIndex, type) {
  const blockDiv = document.createElement('div');
  blockDiv.className = 'card mb-4';
  
  let minScoreInput = '';
  if (type === 'bonus') {
    minScoreInput = `
      <div class="mb-3">
        <label class="form-label">Минимальный балл для доступа:</label>
        <input type="number" class="form-control" value="${block.min_score || 0}" 
               onchange="updateMinScore(${blockIndex}, '${type}', this.value)">
      </div>
    `;
  }
  
  blockDiv.innerHTML = `
    <div class="card-header d-flex justify-content-between align-items-center">
      <h5>${type === 'bonus' ? '🎁 Бонусный блок' : '📋 Обычный блок'} ${blockIndex + 1}</h5>
      <button class="btn btn-danger btn-sm" onclick="removeBlock(${blockIndex}, '${type}')">
        Удалить блок
      </button>
    </div>
    <div class="card-body">
      <div class="mb-3">
        <label class="form-label">Заголовок блока:</label>
        <input type="text" class="form-control" value="${block.title || ''}" 
               onchange="updateBlockTitle(${blockIndex}, '${type}', this.value)">
      </div>
      
      ${minScoreInput}
      
      <div class="mb-3">
        <label class="form-label">Вопросы:</label>
        <div id="${type}-questions-${blockIndex}">
          ${renderQuestions(block.questions || [], blockIndex, type)}
        </div>
        <button class="btn btn-secondary btn-sm mt-2" onclick="addQuestion(${blockIndex}, '${type}')">
          Добавить вопрос
        </button>
      </div>
      
      <div class="mb-3">
        <label class="form-label">Кнопки после блока:</label>
        <div class="row">
          <div class="col-md-4">
            <label class="form-label">Контакты:</label>
            <input type="url" class="form-control" value="${block.buttons?.contacts || ''}" 
                   onchange="updateButton(${blockIndex}, '${type}', 'contacts', this.value)">
          </div>
          <div class="col-md-4">
            <label class="form-label">Подарок:</label>
            <input type="url" class="form-control" value="${block.buttons?.gift || ''}" 
                   onchange="updateButton(${blockIndex}, '${type}', 'gift', this.value)">
          </div>
          <div class="col-md-4">
            <label class="form-label">Сайт:</label>
            <input type="url" class="form-control" value="${block.buttons?.site || ''}" 
                   onchange="updateButton(${blockIndex}, '${type}', 'site', this.value)">
          </div>
        </div>
      </div>
    </div>
  `;
  
  return blockDiv;
}

function renderQuestions(questions, blockIndex, type) {
  return questions.map((question, qIndex) => `
    <div class="border p-3 mb-3">
      <div class="d-flex justify-content-between align-items-center mb-2">
        <h6>Вопрос ${qIndex + 1}</h6>
        <button class="btn btn-danger btn-sm" onclick="removeQuestion(${blockIndex}, ${qIndex}, '${type}')">
          Удалить
        </button>
      </div>
      
      <div class="mb-3">
        <label class="form-label">Текст вопроса:</label>
        <textarea class="form-control" rows="2" 
                  onchange="updateQuestionText(${blockIndex}, ${qIndex}, '${type}', this.value)">${question.text || ''}</textarea>
      </div>
      
      <div class="row">
        <div class="col-md-8">
          <label class="form-label">Варианты ответов:</label>
          <div class="mb-2">
            <label class="form-label">A:</label>
            <input type="text" class="form-control" value="${question.options?.A || ''}" 
                   onchange="updateOption(${blockIndex}, ${qIndex}, '${type}', 'A', this.value)">
          </div>
          <div class="mb-2">
            <label class="form-label">B:</label>
            <input type="text" class="form-control" value="${question.options?.B || ''}" 
                   onchange="updateOption(${blockIndex}, ${qIndex}, '${type}', 'B', this.value)">
          </div>
          <div class="mb-2">
            <label class="form-label">C:</label>
            <input type="text" class="form-control" value="${question.options?.C || ''}" 
                   onchange="updateOption(${blockIndex}, ${qIndex}, '${type}', 'C', this.value)">
          </div>
        </div>
        
        <div class="col-md-4">
          <label class="form-label">Баллы за ответы:</label>
          <div class="mb-2">
            <label class="form-label">A:</label>
            <select class="form-control" onchange="updateScore(${blockIndex}, ${qIndex}, '${type}', 'A', this.value)">
              <option value="1" ${question.scores?.A === 1 ? 'selected' : ''}>1</option>
              <option value="2" ${question.scores?.A === 2 ? 'selected' : ''}>2</option>
              <option value="3" ${question.scores?.A === 3 ? 'selected' : ''}>3</option>
            </select>
          </div>
          <div class="mb-2">
            <label class="form-label">B:</label>
            <select class="form-control" onchange="updateScore(${blockIndex}, ${qIndex}, '${type}', 'B', this.value)">
              <option value="1" ${question.scores?.B === 1 ? 'selected' : ''}>1</option>
              <option value="2" ${question.scores?.B === 2 ? 'selected' : ''}>2</option>
              <option value="3" ${question.scores?.B === 3 ? 'selected' : ''}>3</option>
            </select>
          </div>
          <div class="mb-2">
            <label class="form-label">C:</label>
            <select class="form-control" onchange="updateScore(${blockIndex}, ${qIndex}, '${type}', 'C', this.value)">
              <option value="1" ${question.scores?.C === 1 ? 'selected' : ''}>1</option>
              <option value="2" ${question.scores?.C === 2 ? 'selected' : ''}>2</option>
              <option value="3" ${question.scores?.C === 3 ? 'selected' : ''}>3</option>
            </select>
          </div>
        </div>
      </div>
    </div>
  `).join('');
}

// Функции обновления данных
function updateBlockTitle(blockIndex, type, value) {
  const blocks = type === 'bonus' ? data.bonus_blocks : data.blocks;
  blocks[blockIndex].title = value;
}

function updateMinScore(blockIndex, type, value) {
  if (type === 'bonus') {
    data.bonus_blocks[blockIndex].min_score = parseInt(value);
  }
}

function updateQuestionText(blockIndex, qIndex, type, value) {
  const blocks = type === 'bonus' ? data.bonus_blocks : data.blocks;
  blocks[blockIndex].questions[qIndex].text = value;
}

function updateOption(blockIndex, qIndex, type, option, value) {
  const blocks = type === 'bonus' ? data.bonus_blocks : data.blocks;
  if (!blocks[blockIndex].questions[qIndex].options) {
    blocks[blockIndex].questions[qIndex].options = {};
  }
  blocks[blockIndex].questions[qIndex].options[option] = value;
}

function updateScore(blockIndex, qIndex, type, option, value) {
  const blocks = type === 'bonus' ? data.bonus_blocks : data.blocks;
  if (!blocks[blockIndex].questions[qIndex].scores) {
    blocks[blockIndex].questions[qIndex].scores = {};
  }
  blocks[blockIndex].questions[qIndex].scores[option] = parseInt(value);
}

function updateButton(blockIndex, type, buttonType, value) {
  const blocks = type === 'bonus' ? data.bonus_blocks : data.blocks;
  if (!blocks[blockIndex].buttons) {
    blocks[blockIndex].buttons = {};
  }
  blocks[blockIndex].buttons[buttonType] = value;
}

// Функции добавления/удаления
function addBlock(type) {
  const newBlock = {
    title: '',
    type: type,
    questions: [],
    buttons: { contacts: '', gift: '', site: '' }
  };
  
  if (type === 'bonus') {
    newBlock.min_score = 10;
    data.bonus_blocks.push(newBlock);
  } else {
    data.blocks.push(newBlock);
  }
  
  renderBlocks();
}

function removeBlock(blockIndex, type) {
  if (confirm('Удалить этот блок?')) {
    if (type === 'bonus') {
      data.bonus_blocks.splice(blockIndex, 1);
    } else {
      data.blocks.splice(blockIndex, 1);
    }
    renderBlocks();
  }
}

function addQuestion(blockIndex, type) {
  const blocks = type === 'bonus' ? data.bonus_blocks : data.blocks;
  const newQuestion = {
    text: '',
    options: { A: '', B: '', C: '' },
    scores: { A: 1, B: 2, C: 3 }
  };
  
  blocks[blockIndex].questions.push(newQuestion);
  renderBlocks();
}

function removeQuestion(blockIndex, qIndex, type) {
  if (confirm('Удалить этот вопрос?')) {
    const blocks = type === 'bonus' ? data.bonus_blocks : data.blocks;
    blocks[blockIndex].questions.splice(qIndex, 1);
    renderBlocks();
  }
}

// Сохранение данных
async function saveData() {
  try {
    const response = await fetch('/api/questions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    
    if (response.ok) {
      const status = document.getElementById('save-status');
      status.classList.remove('d-none');
      setTimeout(() => status.classList.add('d-none'), 3000);
    } else {
      alert('Ошибка сохранения!');
    }
  } catch (error) {
    console.error('Ошибка:', error);
    alert('Ошибка сохранения!');
  }
}
