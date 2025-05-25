from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, jsonify
)
from auth import login_required
from database import get_db
import random
from datetime import datetime, timedelta
import math

bp = Blueprint('game', __name__, url_prefix='/game')

@bp.route('/', methods=('GET', 'POST'))
def game():
    # This route renders the game page
    return render_template('game.html')

@bp.route('/fetch-paper', methods=['GET'])
def fetch_paper():
    """Fetch a random paper from the database for the game."""
    db = get_db()
    paper = db.execute(
        'SELECT id, abstract, date FROM papers ORDER BY RANDOM() LIMIT 1'
    ).fetchone()
    
    if paper is None:
        # If no papers in database, return dummy data
        return jsonify({
            'id': 0,
            'abstract': 'No papers found in the database. Please add some papers first.',
            'date': '2020-01-01'
        })
    
    # Convert to dictionary
    paper_dict = {
        'id': paper['id'],
        'abstract': paper['abstract'],
        'date': paper['date']
    }
    
    return jsonify(paper_dict)

@bp.route('/submit-score', methods=['POST'])
def submit_score():
    """Submit a game score."""
    if g.user is None:
        return jsonify({'status': 'error', 'message': 'You must be logged in to submit scores'}), 401
    
    data = request.get_json()
    score = data.get('score', 0)
    
    db = get_db()
    
    # Update the user's high score if the new score is higher
    current_high_score = db.execute(
        'SELECT high_score FROM users WHERE id = ?', (g.user['id'],)
    ).fetchone()['high_score'] or 0
    
    if score > current_high_score:
        db.execute(
            'UPDATE users SET high_score = ? WHERE id = ?',
            (score, g.user['id'])
        )
        db.commit()
        return jsonify({'status': 'success', 'message': 'New high score!'})
    
    return jsonify({'status': 'success', 'message': 'Score submitted'})

@bp.route('/calculate-score', methods=['POST'])
def calculate_score():
    """
    Calculate the score based on how close the guess is to the actual date.
    
    New scoring system:
    - Within 6 months (182.5 days): Full 100 points
    - 6 months to 3 years (1095 days): Linear drop from 100 to 0 points
    - Beyond 3 years: 0 points
    """
    data = request.get_json()
    actual_date_str = data.get('actual_date', '')
    guess_date_str = data.get('guess_date', '')
    
    # Parse dates
    try:
        # Handle different date formats
        try:
            actual_date = datetime.strptime(actual_date_str, '%Y-%m-%d')
        except ValueError:
            # Try alternative format (YYYY-MM)
            actual_date = datetime.strptime(actual_date_str, '%Y-%m')
            
        guess_date = datetime.strptime(guess_date_str, '%Y-%m-%d')
        
        # Calculate difference in days
        difference_days = abs((actual_date - guess_date).days)
        
        # New scoring thresholds
        FULL_POINTS_THRESHOLD = 182.5  # 6 months (365.25 / 2)
        ZERO_POINTS_THRESHOLD = 1095   # 3 years (365.25 * 3)
        LINEAR_RANGE = ZERO_POINTS_THRESHOLD - FULL_POINTS_THRESHOLD  # 912.5 days
        MAX_SCORE = 100
        
        # Calculate score based on new system
        if difference_days <= FULL_POINTS_THRESHOLD:
            # Within 6 months: full points
            score = MAX_SCORE
            category = "Perfect Range"
            explanation = "Within 6 months - full points!"
        elif difference_days >= ZERO_POINTS_THRESHOLD:
            # Beyond 3 years: zero points
            score = 0
            category = "No Points"
            explanation = "More than 3 years off - no points"
        else:
            # Linear interpolation between full points and zero
            excess_days = difference_days - FULL_POINTS_THRESHOLD
            score_reduction = (excess_days / LINEAR_RANGE) * MAX_SCORE
            score = MAX_SCORE - score_reduction
            score = max(0, int(round(score)))
            
            category = "Partial Points"
            years_off = difference_days / 365.25
            explanation = f"About {years_off:.1f} years off - partial points"
        
        # Format the actual date for response
        if len(actual_date_str) <= 7:
            # Keep original format if it was YYYY-MM
            formatted_actual_date = actual_date_str
        else:
            # Use full date format
            formatted_actual_date = actual_date.strftime('%Y-%m-%d')
        
        return jsonify({
            'status': 'success', 
            'score': int(score), 
            'difference_days': difference_days,
            'actual_date': formatted_actual_date,
            'category': category,
            'explanation': explanation,
            'max_possible': MAX_SCORE,
            'scoring_details': {
                'full_points_threshold_days': FULL_POINTS_THRESHOLD,
                'zero_points_threshold_days': ZERO_POINTS_THRESHOLD,
                'within_full_range': difference_days <= FULL_POINTS_THRESHOLD,
                'years_difference': round(difference_days / 365.25, 2)
            }
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error', 
            'message': f'Error calculating score: {str(e)}'
        }), 400

def calculate_paper_score(actual_date, guess_date, max_points=100):
    """
    Helper function to calculate score for a single paper guess.
    Can be used for testing or other scoring calculations.
    
    Args:
        actual_date (datetime or str): The actual publication date
        guess_date (datetime or str): The user's guessed date
        max_points (int): Maximum points possible (default: 100)
    
    Returns:
        dict: Contains score and detailed information
    """
    # Convert strings to datetime objects if needed
    if isinstance(actual_date, str):
        try:
            actual_date = datetime.strptime(actual_date, '%Y-%m-%d')
        except ValueError:
            actual_date = datetime.strptime(actual_date, '%Y-%m')
            
    if isinstance(guess_date, str):
        guess_date = datetime.strptime(guess_date, '%Y-%m-%d')
    
    # Calculate difference
    difference_days = abs((actual_date - guess_date).days)
    
    # Scoring thresholds
    FULL_POINTS_THRESHOLD = 182.5  # 6 months
    ZERO_POINTS_THRESHOLD = 1095   # 3 years
    LINEAR_RANGE = ZERO_POINTS_THRESHOLD - FULL_POINTS_THRESHOLD
    
    if difference_days <= FULL_POINTS_THRESHOLD:
        score = max_points
        category = "Perfect Range"
    elif difference_days >= ZERO_POINTS_THRESHOLD:
        score = 0
        category = "No Points"
    else:
        excess_days = difference_days - FULL_POINTS_THRESHOLD
        score_reduction = (excess_days / LINEAR_RANGE) * max_points
        score = max_points - score_reduction
        score = max(0, int(round(score)))
        category = "Partial Points"
    
    return {
        'score': score,
        'difference_days': difference_days,
        'category': category,
        'years_difference': round(difference_days / 365.25, 2)
    }

# Optional route for adding papers (for testing purposes)
@bp.route('/add-sample-paper', methods=['GET'])
def add_sample_paper():
    """Add a sample paper to the database for testing."""
    db = get_db()
    
    # Sample papers data with various dates
    sample_papers = [
        {
            'abstract': 'This paper explores deep learning techniques for natural language processing, focusing on transformer architectures that have demonstrated remarkable performance on a wide range of tasks.',
            'date': '2020-06-15',
            'citations': '218',
            'arxiv_id': 'sample123',
            'keywords': 'deep learning, NLP, transformers',
            'keyword_sum': 3
        },
        {
            'abstract': 'We propose a novel approach to reinforcement learning that combines model-based planning with model-free policy optimization, showing improvements on challenging control tasks.',
            'date': '2018-03-22',
            'citations': '167',
            'arxiv_id': 'sample124',
            'keywords': 'reinforcement learning, model-based planning, control',
            'keyword_sum': 3
        },
        {
            'abstract': 'This study examines the role of quantum computing in solving complex optimization problems, particularly those intractable for classical computers.',
            'date': '2022-11-05',
            'citations': '42',
            'arxiv_id': 'sample125',
            'keywords': 'quantum computing, optimization',
            'keyword_sum': 2
        },
        {
            'abstract': 'We investigate privacy-preserving techniques for federated learning, enabling collaborative model training while maintaining data confidentiality.',
            'date': '2021-08-17',
            'citations': '83',
            'arxiv_id': 'sample126',
            'keywords': 'federated learning, privacy',
            'keyword_sum': 2
        },
        {
            'abstract': 'This paper presents a comprehensive analysis of convolutional neural networks for image classification, proposing architectural modifications that improve accuracy.',
            'date': '2016-05-12',
            'citations': '1245',
            'arxiv_id': 'sample127',
            'keywords': 'CNN, image classification',
            'keyword_sum': 2
        },
        {
            'abstract': 'We introduce a new dataset for sentiment analysis in social media posts, annotated with fine-grained emotional categories beyond simple polarity.',
            'date': '2019-02-08',
            'citations': '132',
            'arxiv_id': 'sample128',
            'keywords': 'sentiment analysis, dataset, social media',
            'keyword_sum': 3
        },
        {
            'abstract': 'This research explores the application of graph neural networks to molecular property prediction, with implications for drug discovery.',
            'date': '2021-11-29',
            'citations': '56',
            'arxiv_id': 'sample129',
            'keywords': 'GNN, molecular properties, drug discovery',
            'keyword_sum': 3
        }
    ]
    
    # Insert all sample papers
    for paper in sample_papers:
        db.execute(
            '''
            INSERT INTO papers (abstract, date, citations, arxiv_id, keywords, keyword_sum)
            VALUES (?, ?, ?, ?, ?, ?)
            ''',
            (
                paper['abstract'], 
                paper['date'],
                paper['citations'],
                paper['arxiv_id'],
                paper['keywords'],
                paper['keyword_sum']
            )
        )
    
    db.commit()
    
    return jsonify({'status': 'success', 'message': f'Added {len(sample_papers)} sample papers'})

# Optional testing route to verify scoring system
@bp.route('/test-scoring', methods=['GET'])
def test_scoring():
    """Test route to verify the new scoring system works correctly."""
    
    test_cases = [
        ("2023-01-01", "2023-01-01"),    # Perfect match
        ("2023-01-01", "2023-03-01"),    # 2 months off
        ("2023-01-01", "2023-07-01"),    # 6 months off (edge of full points)
        ("2023-01-01", "2024-01-01"),    # 1 year off
        ("2023-01-01", "2024-07-01"),    # 1.5 years off
        ("2023-01-01", "2025-01-01"),    # 2 years off
        ("2023-01-01", "2025-07-01"),    # 2.5 years off
        ("2023-01-01", "2026-01-01"),    # 3 years off (edge of zero points)
        ("2023-01-01", "2027-01-01"),    # 4 years off
    ]
    
    results = []
    for actual, guess in test_cases:
        result = calculate_paper_score(actual, guess)
        results.append({
            'actual_date': actual,
            'guess_date': guess,
            'difference_days': result['difference_days'],
            'score': result['score'],
            'category': result['category'],
            'years_difference': result['years_difference']
        })
    
    return jsonify({
        'status': 'success',
        'message': 'Scoring system test results',
        'test_results': results,
        'scoring_info': {
            'full_points_range': '0-6 months (0-182.5 days)',
            'partial_points_range': '6 months-3 years (182.5-1095 days)',
            'zero_points_range': '3+ years (1095+ days)'
        }
    })