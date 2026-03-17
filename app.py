from flask import Flask, render_template, request, jsonify
import json
import sys
import os

# Добавляем текущую директорию в путь поиска модулей
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'model'))

# Теперь импортируем predictor
from model.predictor import DotaPredictor

app = Flask(__name__)

# Загрузка модели
predictor = DotaPredictor()
try:
    predictor.load('model/saved_model.pkl')
    print("✅ Модель загружена")
except Exception as e:
    print(f"⚠️ Ошибка загрузки модели: {e}")
    print("💡 Убедитесь что запустили: python model/trainer.py")

# Загрузка команд
def load_teams():
    try:
        with open('teams.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

TEAMS_DATA = load_teams()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/teams')
def get_teams():
    return jsonify(TEAMS_DATA)

@app.route('/api/team/search', methods=['POST'])
def search_team():
    """Поиск команды"""
    data = request.get_json()
    team_name = data.get('name', '').strip().lower()
    
    if not team_name:
        return jsonify({'error': 'Введите название', 'success': False}), 400
    
    found = None
    for team in TEAMS_DATA:
        if (team.get('team_name', '').lower().find(team_name) >= 0 or 
            team.get('team_tag', '').lower() == team_name):
            found = team
            break
    
    if not found:
        return jsonify({'error': 'Команда не найдена', 'success': False}), 404
    
    return jsonify({
        'success': True,
        'team': {
            'team_id': found.get('team_id'),
            'team_name': found.get('team_name'),
            'team_tag': found.get('team_tag'),
            'players': found.get('current_players', [])
        }
    })

@app.route('/api/predict', methods=['POST'])
def predict():
    """Предсказание исхода матча"""
    data = request.get_json()
    
    dire = data.get('dire', {})
    radiant = data.get('radiant', {})
    
    # Извлекаем ID команд
    dire_team_id = dire.get('team_id', 0)
    radiant_team_id = radiant.get('team_id', 0)
    
    # Извлекаем героев (hero_id)
    dire_heroes = [p.get('hero_id', 0) for p in dire.get('players_with_heroes', []) if p.get('hero_id')]
    radiant_heroes = [p.get('hero_id', 0) for p in radiant.get('players_with_heroes', []) if p.get('hero_id')]
    
    # Извлекаем игроков (account_id)
    dire_players = [p.get('account_id', 0) for p in dire.get('players_with_heroes', []) if p.get('account_id')]
    radiant_players = [p.get('account_id', 0) for p in radiant.get('players_with_heroes', []) if p.get('account_id')]
    
    # Проверка данных
    if not dire_heroes or not radiant_heroes:
        return jsonify({
            'error': 'Введите героев для всех игроков',
            'success': False
        }), 400
    
    try:
        # Предсказание
        prediction = predictor.predict_match(
            radiant_team_id=radiant_team_id,
            dire_team_id=dire_team_id,
            radiant_heroes=radiant_heroes,
            dire_heroes=dire_heroes,
            radiant_players=radiant_players if radiant_players else None,
            dire_players=dire_players if dire_players else None
        )
        
        prediction['success'] = True
        prediction['dire_team_name'] = dire.get('team_name', 'Unknown')
        prediction['radiant_team_name'] = radiant.get('team_name', 'Unknown')
        
        return jsonify(prediction)
        
    except Exception as e:
        print(f"❌ Ошибка предсказания: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': 'Ошибка при предсказании',
            'success': False
        }), 500

if __name__ == '__main__':
    print("🎮 Dota Predictor Server")
    print("📍 http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)