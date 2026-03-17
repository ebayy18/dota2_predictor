// Глобальные переменные
let direTeam = null;
let radiantTeam = null;
let heroMapping = {};

// Инициализация (безопасная для браузера и Telegram)
function initApp() {
    // Проверяем Telegram WebApp
    if (window.Telegram && window.Telegram.WebApp) {
        const tg = window.Telegram.WebApp;
        tg.expand();
        tg.ready();
        console.log('✅ Telegram WebApp initialized');
    } else {
        console.log('ℹ️ Running in browser (not Telegram)');
    }
    
    // Загружаем героев
    loadHeroes();
    
    // Настраиваем обработчики
    setupEventListeners();
    
    console.log('✅ App initialized');
}

// Загрузка списка героев
async function loadHeroes() {
    try {
        const response = await fetch('https://api.opendota.com/api/heroStats');
        const heroes = await response.json();
        
        heroMapping = {};
        heroes.forEach(hero => {
            heroMapping[hero.localized_name.toLowerCase()] = hero.id;
        });
        
        console.log(`✅ Loaded ${heroes.length} heroes`);
    } catch (error) {
        console.error('❌ Error loading heroes:', error);
    }
}

// Настройка обработчиков событий
function setupEventListeners() {
    const direSearchBtn = document.getElementById('direSearchBtn');
    const radiantSearchBtn = document.getElementById('radiantSearchBtn');
    const direInput = document.getElementById('direInput');
    const radiantInput = document.getElementById('radiantInput');
    const predictBtn = document.getElementById('predictBtn');
    
    // Кнопки поиска
    if (direSearchBtn) {
        direSearchBtn.addEventListener('click', () => searchTeam('dire'));
    }
    
    if (radiantSearchBtn) {
        radiantSearchBtn.addEventListener('click', () => searchTeam('radiant'));
    }
    
    // Enter в полях
    if (direInput) {
        direInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') searchTeam('dire');
        });
    }
    
    if (radiantInput) {
        radiantInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') searchTeam('radiant');
        });
    }
    
    // Кнопка предсказания
    if (predictBtn) {
        predictBtn.addEventListener('click', predict);
    }
}

// Поиск команды
async function searchTeam(teamType) {
    const inputId = teamType === 'dire' ? 'direInput' : 'radiantInput';
    const errorId = teamType === 'dire' ? 'direError' : 'radiantError';
    const playersId = teamType === 'dire' ? 'direPlayers' : 'radiantPlayers';
    
    const input = document.getElementById(inputId);
    const errorDiv = document.getElementById(errorId);
    const playersDiv = document.getElementById(playersId);
    
    if (!input || !errorDiv || !playersDiv) {
        console.error(`Elements not found for ${teamType}`);
        return;
    }
    
    const teamName = input.value.trim();
    
    if (!teamName) {
        errorDiv.textContent = 'Введите название команды';
        errorDiv.style.color = '#e74c3c';
        return;
    }
    
    try {
        console.log(`🔍 Searching for team: ${teamName}`);
        
        const response = await fetch('/api/team/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name: teamName })
        });
        
        const data = await response.json();
        console.log('Response:', data);
        
        if (!data.success) {
            errorDiv.textContent = data.error || 'Команда не найдена';
            errorDiv.style.color = '#e74c3c';
            playersDiv.innerHTML = '';
            
            if (teamType === 'dire') direTeam = null;
            else radiantTeam = null;
            return;
        }
        
        // Команда найдена
        errorDiv.textContent = '';
        
        if (teamType === 'dire') {
            direTeam = data.team;
        } else {
            radiantTeam = data.team;
        }
        
        renderPlayers(playersDiv, data.team.players, teamType);
        
    } catch (error) {
        console.error('Search error:', error);
        errorDiv.textContent = 'Ошибка подключения к серверу';
        errorDiv.style.color = '#e74c3c';
    }
}

// Отрисовка полей игроков
function renderPlayers(container, players, teamType) {
    container.innerHTML = '';
    
    if (!players || players.length === 0) {
        container.innerHTML = '<p style="color: #616b79; text-align: center; margin-top: 10px;">Нет данных об игроках</p>';
        return;
    }
    
    players.forEach((player, index) => {
        const row = document.createElement('div');
        row.className = 'player-row';
        row.style.cssText = 'display: flex; align-items: center; gap: 10px; margin-bottom: 10px; padding: 10px; background: white; border-radius: 10px;';
        
        row.innerHTML = `
            <span style="flex: 1; font-weight: 600; color: #555; font-size: 14px;">
                ${index + 1}. ${escapeHtml(player.name)}
            </span>
            <input type="text" 
                   class="player-hero" 
                   data-account-id="${player.account_id}"
                   data-team="${teamType}"
                   placeholder="Герой..."
                   list="hero-list-${teamType}-${index}"
                   style="flex: 1.5; padding: 8px 15px; border: 2px solid #e0e0e0; border-radius: 15px; font-size: 14px;">
            <datalist id="hero-list-${teamType}-${index}">
                ${getHeroOptions()}
            </datalist>
        `;
        
        container.appendChild(row);
    });
}

// Опции героев для datalist
function getHeroOptions() {
    const heroes = [
        'Anti-Mage', 'Axe', 'Bane', 'Bloodseeker', 'Crystal Maiden', 'Drow Ranger',
        'Earthshaker', 'Juggernaut', 'Mirana', 'Morphling', 'Shadow Fiend', 'Phantom Lancer',
        'Puck', 'Pudge', 'Razor', 'Sand King', 'Storm Spirit', 'Sven', 'Tiny', 'Vengeful Spirit',
        'Windranger', 'Zeus', 'Kunkka', 'Lina', 'Lion', 'Shadow Shaman', 'Slardar', 'Tidehunter',
        'Witch Doctor', 'Lich', 'Riki', 'Enigma', 'Tinker', 'Sniper', 'Necrophos', 'Warlock',
        'Beastmaster', 'Queen of Pain', 'Venomancer', 'Faceless Void', 'Wraith King',
        'Death Prophet', 'Phantom Assassin', 'Pugna', 'Templar Assassin', 'Viper', 'Luna',
        'Dragon Knight', 'Dazzle', 'Clockwerk', 'Leshrac', "Nature's Prophet", 'Lifestealer',
        'Dark Seer', 'Clinkz', 'Omniknight', 'Enchantress', 'Huskar', 'Night Stalker', 'Broodmother',
        'Bounty Hunter', 'Weaver', 'Jakiro', 'Batrider', 'Chen', 'Spectre', 'Ancient Apparition',
        'Doom', 'Ursa', 'Spirit Breaker', 'Gyrocopter', 'Alchemist', 'Invoker', 'Silencer',
        'Outworld Destroyer', 'Lycan', 'Brewmaster', 'Shadow Demon', 'Lone Druid', 'Chaos Knight',
        'Meepo', 'Treant Protector', 'Ogre Magi', 'Undying', 'Rubick', 'Disruptor', 'Nyx Assassin',
        'Naga Siren', 'Keeper of the Light', 'Io', 'Visage', 'Slark', 'Medusa', 'Troll Warlord',
        'Centaur Warrunner', 'Magnus', 'Timbersaw', 'Bristleback', 'Tusk', 'Skywrath Mage',
        'Abaddon', 'Elder Titan', 'Legion Commander', 'Techies', 'Ember Spirit', 'Earth Spirit',
        'Underlord', 'Terrorblade', 'Phoenix', 'Oracle', 'Winter Wyvern', 'Arc Warden', 'Monkey King',
        'Dark Willow', 'Pangolier', 'Grimstroke', 'Hoodwink', 'Void Spirit', 'Snapfire', 'Mars',
        'Dawnbreaker', 'Marci', 'Primal Beast', 'Muerta'
    ];
    
    return heroes.map(h => `<option value="${h}">`).join('');
}

async function predict() {
    if (!direTeam || !radiantTeam) {
        alert('Выберите обе команды!');
        return;
    }
    
    const direData = collectTeamData('dire');
    const radiantData = collectTeamData('radiant');
    
    // Проверяем что заполнено ровно 5 героев
    if (direData.players_with_heroes.length !== 5) {
        alert(`❌ Для Team Dire нужно выбрать ровно 5 героев (сейчас: ${direData.players_with_heroes.length})`);
        return;
    }
    
    if (radiantData.players_with_heroes.length !== 5) {
        alert(`❌ Для Team Radiant нужно выбрать ровно 5 героев (сейчас: ${radiantData.players_with_heroes.length})`);
        return;
    }
    
    const predictBtn = document.getElementById('predictBtn');
    predictBtn.disabled = true;
    predictBtn.textContent = '⏳ Анализируем...';
    
    try {
        console.log('🔮 Отправка предсказания...');
        console.log('Dire:', direData);
        console.log('Radiant:', radiantData);
        
        const response = await fetch('/api/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                dire: direData,
                radiant: radiantData
            })
        });
        
        console.log('Response status:', response.status);
        const data = await response.json();
        console.log('Prediction result:', data);
        
        if (data.success) {
            showResult(data);
        } else {
            alert('❌ ' + (data.error || 'Ошибка предсказания'));
        }
        
    } catch (error) {
        console.error('Prediction error:', error);
        alert('❌ Ошибка подключения к серверу. Проверьте консоль (F12).');
    } finally {
        predictBtn.disabled = false;
        predictBtn.textContent = '🔮 Предсказать победителя';
    }
}


// Сбор данных команды
function collectTeamData(teamType) {
    const containerId = teamType === 'dire' ? 'direPlayers' : 'radiantPlayers';
    const container = document.getElementById(containerId);
    const inputs = container.querySelectorAll('.player-hero');
    
    const players = Array.from(inputs).map(input => ({
        account_id: parseInt(input.dataset.accountId),
        name: input.previousElementSibling.textContent.replace(/^\d+\.\s*/, ''),
        hero_name: input.value.trim(),
        hero_id: heroNameToId(input.value.trim())
    })).filter(p => p.hero_id > 0);
    
    const team = teamType === 'dire' ? direTeam : radiantTeam;
    
    return {
        team_id: team.team_id,
        team_name: team.team_name,
        players_with_heroes: players
    };
}

// Конвертация имени героя в ID
function heroNameToId(name) {
    if (!name) return 0;
    return heroMapping[name.toLowerCase()] || 0;
}

// Показ результата
function showResult(data) {
    console.log('📊 showResult called with:', data);
    
    const resultContainer = document.getElementById('result');
    if (!resultContainer) {
        console.error('❌ Result container not found!');
        return;
    }
    
    const winnerName = data.winner === 'radiant' ? 
        data.radiant_team_name : data.dire_team_name;
    const winnerColor = data.winner === 'radiant' ? '#27ae60' : '#e74c3c';
    
    console.log(`🏆 Winner: ${winnerName}, Color: ${winnerColor}`);
    
    const html = `
        <div style="margin-top: 20px; padding: 25px; background: white; border-radius: 15px; text-align: center; animation: fadeIn 0.5s; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
            <div style="font-size: 28px; margin-bottom: 20px; color: ${winnerColor}; font-weight: bold;">
                🏆 Победитель: ${winnerName}
            </div>
            
            <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 15px 0;">
                <div style="font-size: 22px; color: #e74c3c; margin: 10px 0; font-weight: bold;">
                    🔴 ${data.dire_team_name}: ${data.dire_win_chance}%
                </div>
                <div style="font-size: 22px; color: #27ae60; margin: 10px 0; font-weight: bold;">
                    🟢 ${data.radiant_team_name}: ${data.radiant_win_chance}%
                </div>
            </div>
            
            <div style="margin-top: 20px; padding: 15px; background: #e3f2fd; border-radius: 10px;">
                <div style="color: #1976d2; font-size: 16px; margin-bottom: 10px;">
                    📊 Статистика:
                </div>
                <div style="color: #666; font-size: 14px; text-align: left;">
                    <div>• Разница команд: ${data.factors.team_wr_diff > 0 ? '+' : ''}${data.factors.team_wr_diff}%</div>
                    <div>• Разница героев: ${data.factors.hero_wr_diff > 0 ? '+' : ''}${data.factors.hero_wr_diff}%</div>
                    <div>• Разница игроков: ${data.factors.player_wr_diff > 0 ? '+' : ''}${data.factors.player_wr_diff}%</div>
                    ${data.factors.h2h_matches > 0 ? `<div>• H2H: ${data.factors.h2h_radiant_wr}% (матчей: ${data.factors.h2h_matches})</div>` : ''}
                </div>
            </div>
            
            <div style="margin-top: 15px; color: #666; font-size: 14px;">
                Уверенность модели: <strong>${data.confidence}%</strong>
            </div>
        </div>
    `;
    
    console.log('📝 Setting HTML:', html.substring(0, 100) + '...');
    resultContainer.innerHTML = html;
    resultContainer.style.display = 'block';
    resultContainer.classList.add('show');
    
    // Прокрутка к результату
    setTimeout(() => {
        resultContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        console.log('✅ Result displayed');
    }, 100);
}

// Экранирование HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Запуск при загрузке страницы
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
} else {
    initApp();
}