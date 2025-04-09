from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from models import db, CTFChallenge, ChallengeSolve, ChallengeHint
from datetime import datetime

ctf = Blueprint('ctf', __name__)

@ctf.route('/ctf')
def ctf_home():
    challenges = CTFChallenge.query.filter_by(is_active=True).all()
    categories = set(c.category for c in challenges)
    return render_template('ctf/home.html', challenges=challenges, categories=categories)

@ctf.route('/ctf/challenge/<int:challenge_id>')
@login_required
def challenge_detail(challenge_id):
    challenge = CTFChallenge.query.get_or_404(challenge_id)
    solved = ChallengeSolve.query.filter_by(
        user_id=current_user.id,
        challenge_id=challenge_id
    ).first() is not None
    return render_template('ctf/challenge.html', challenge=challenge, solved=solved)

@ctf.route('/ctf/submit/<int:challenge_id>', methods=['POST'])
@login_required
def submit_flag(challenge_id):
    challenge = CTFChallenge.query.get_or_404(challenge_id)
    flag = request.form.get('flag')
    
    if not flag:
        flash('Please submit a flag', 'error')
        return redirect(url_for('ctf.challenge_detail', challenge_id=challenge_id))
    
    # Check if already solved
    if ChallengeSolve.query.filter_by(
        user_id=current_user.id,
        challenge_id=challenge_id
    ).first():
        flash('You have already solved this challenge!', 'info')
        return redirect(url_for('ctf.challenge_detail', challenge_id=challenge_id))
    
    if flag == challenge.flag:
        # Record the solve
        solve = ChallengeSolve(user_id=current_user.id, challenge_id=challenge_id)
        current_user.points += challenge.points
        db.session.add(solve)
        db.session.commit()
        flash(f'Correct! You earned {challenge.points} points!', 'success')
    else:
        flash('Incorrect flag, try again!', 'error')
    
    return redirect(url_for('ctf.challenge_detail', challenge_id=challenge_id))

@ctf.route('/ctf/leaderboard')
def leaderboard():
    users = User.query.order_by(User.points.desc()).limit(10).all()
    return render_template('ctf/leaderboard.html', users=users)

@ctf.route('/ctf/hint/<int:hint_id>')
@login_required
def get_hint(hint_id):
    hint = ChallengeHint.query.get_or_404(hint_id)
    if current_user.points >= hint.cost:
        current_user.points -= hint.cost
        db.session.commit()
        return jsonify({'hint': hint.content})
    return jsonify({'error': 'Not enough points'}), 400

# Admin routes
@ctf.route('/ctf/admin/challenges', methods=['GET', 'POST'])
@login_required
def admin_challenges():
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('ctf.ctf_home'))
    
    if request.method == 'POST':
        challenge = CTFChallenge(
            title=request.form['title'],
            description=request.form['description'],
            category=request.form['category'],
            points=int(request.form['points']),
            flag=request.form['flag'],
            difficulty=request.form['difficulty']
        )
        db.session.add(challenge)
        db.session.commit()
        flash('Challenge created successfully!', 'success')
        return redirect(url_for('ctf.admin_challenges'))
    
    challenges = CTFChallenge.query.all()
    return render_template('ctf/admin/challenges.html', challenges=challenges)
