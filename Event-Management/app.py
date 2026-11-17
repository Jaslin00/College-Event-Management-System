import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = 'super_secret_event_hub_key'

# Mock Database matching usernames in static/uploads
users = {
    "soman": {
        "user_id": "soman", 
        "name": "Soman", 
        "college_id": "C-2026-001", 
        "email": "soman@college.edu", 
        "major": "Computer Science", 
        "role": "student", 
        "avatar": "uploads/soman_profile.jpg"
    },
    "kuttan": {
        "user_id": "kuttan", 
        "name": "Kuttan", 
        "college_id": "C-2026-002", 
        "email": "kuttan@college.edu", 
        "major": "Mechanical Engineering", 
        "role": "student", 
        "avatar": "uploads/kuttan_profile.jpg"
    },
    "kali": {
        "user_id": "kali", 
        "name": "Kali", 
        "college_id": "C-2026-003", 
        "email": "kali@college.edu", 
        "major": "Electrical Engineering", 
        "role": "student", 
        "avatar": "uploads/kali_profile.jpg"
    },
    "Manui": {
        "user_id": "Manui", 
        "name": "Manui", 
        "college_id": "C-2026-004", 
        "email": "manui@college.edu", 
        "major": "Civil Engineering", 
        "role": "student", 
        "avatar": "uploads/Manui_profile.jpg"
    },
    "organizer": {
        "user_id": "organizer", 
        "name": "Admin", 
        "college_id": "ADM-001", 
        "email": "admin@eventhub.edu", 
        "major": "N/A", 
        "role": "organizer", 
        "avatar": "uploads/admin_profile.jpg"
    }
}

events = [
    {
        "id": 1,
        "name": "Hackathon 2026",
        "date": datetime(2026, 6, 15),
        "time": "09:00 AM",
        "description": "Unleash your creativity and coding skills in this 24-hour hackathon. Build innovative solutions, collaborate with peers, and win exciting prizes!",
        "participants": ["soman", "kuttan"]
    },
    {
        "id": 2,
        "name": "Tech Talk: Future of AI",
        "date": datetime(2026, 6, 20),
        "time": "02:00 PM",
        "description": "Join industry experts as they discuss the future of Artificial Intelligence, agentic workflows, and the next generation of large language models.",
        "participants": ["soman", "kali", "Manui"]
    },
    {
        "id": 3,
        "name": "Annual Career Fair",
        "date": datetime(2026, 6, 25),
        "time": "10:00 AM",
        "description": "Connect with top employers, explore internship opportunities, and jumpstart your career. Bring your resume and dress to impress!",
        "participants": ["kuttan", "kali"]
    }
]

scoreboard = [
    {"team": "Team A", "score": 100},
    {"team": "Team B", "score": 85},
    {"team": "Team C", "score": 95},
]

# Helper decorator for login check
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@login_required
def home():
    user_id = session.get('user_id')
    
    # Calculate stats
    total_events = len(events)
    # Total unique participants across all events
    all_participants = set()
    for ev in events:
        all_participants.update(ev['participants'])
    total_participants = len(all_participants)
    
    # Count registration for current student
    user_registrations = 0
    if user_id != 'organizer':
        user_registrations = sum(1 for ev in events if user_id in ev['participants'])
        
    # Sort events to show recent/upcoming ones
    recent_events = sorted(events, key=lambda x: x['date'])[:5]
    
    return render_template(
        'dashboard.html',
        total_events=total_events,
        total_participants=total_participants,
        user_registrations=user_registrations,
        recent_events=recent_events
    )

@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('user_id'):
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        if user_id in users:
            session['user_id'] = user_id
            session['username'] = users[user_id]['name']
            session['role'] = users[user_id]['role']
            flash(f"Welcome back, {users[user_id]['name']}!", "success")
            return redirect(url_for('home'))
        else:
            flash("Invalid User ID.", "error")
            
    return render_template('login.html', available_users=users.values())

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

@app.route('/events')
@login_required
def event_list():
    user_id = session.get('user_id')
    return render_template('events.html', events=events, user_id=user_id)

@app.route('/event/<int:event_id>')
@login_required
def event_details(event_id):
    event = next((e for e in events if e['id'] == event_id), None)
    if not event:
        return "Event not found", 404
        
    user_id = session.get('user_id')
    is_registered = user_id in event['participants']
    participants_count = len(event['participants'])
    
    return render_template(
        'event_details.html',
        event=event,
        participants_count=participants_count,
        is_registered=is_registered
    )

@app.route('/event/<int:event_id>/register')
@login_required
def register_activity(event_id):
    event = next((e for e in events if e['id'] == event_id), None)
    if not event:
        return "Event not found", 404
        
    user_id = session.get('user_id')
    if user_id == 'organizer':
        flash("Organizers cannot register for events.", "error")
        return redirect(url_for('event_details', event_id=event_id))
        
    if user_id not in event['participants']:
        event['participants'].append(user_id)
        flash(f"Successfully registered for {event['name']}!", "success")
    else:
        flash("You are already registered for this event.", "info")
        
    return redirect(url_for('event_details', event_id=event_id))

@app.route('/event/<int:event_id>/participants')
@login_required
def view_participants(event_id):
    if session.get('role') != 'organizer':
        flash("Access denied: Organizers only.", "error")
        return redirect(url_for('home'))
        
    event = next((e for e in events if e['id'] == event_id), None)
    if not event:
        return "Event not found", 404
        
    # Get user details for participants
    participant_details = [users[uid] for uid in event['participants'] if uid in users]
    
    return render_template(
        'event_participants.html',
        event=event,
        participants=participant_details
    )

@app.route('/add-event', methods=['GET', 'POST'])
@login_required
def add_event():
    if session.get('role') != 'organizer':
        flash("Access denied: Organizers only.", "error")
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        name = request.form.get('name')
        date_str = request.form.get('date')
        
        try:
            date_val = datetime.strptime(date_str, '%Y-%m-%d')
            new_id = max(e['id'] for e in events) + 1 if events else 1
            
            events.append({
                "id": new_id,
                "name": name,
                "date": date_val,
                "time": "10:00 AM",  # Default time
                "description": "No description provided. Contact organizer for details.",
                "participants": []
            })
            flash(f"Event '{name}' added successfully!", "success")
            return redirect(url_for('event_list'))
        except ValueError:
            flash("Invalid date format. Use YYYY-MM-DD.", "error")
            
    return render_template('add_event.html')

@app.route('/add-score', methods=['GET', 'POST'])
@login_required
def add_score():
    if session.get('role') != 'organizer':
        flash("Access denied: Organizers only.", "error")
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        team = request.form.get('team')
        score = request.form.get('score')
        
        try:
            score_val = int(score)
            # Update score if team exists, else add
            existing = next((s for s in scoreboard if s['team'].lower() == team.lower()), None)
            if existing:
                existing['score'] = score_val
            else:
                scoreboard.append({"team": team, "score": score_val})
                
            flash(f"Score updated for {team}!", "success")
            return redirect(url_for('show_scoreboard'))
        except ValueError:
            flash("Invalid score value.", "error")
            
    return render_template('add_score.html')

@app.route('/scoreboard')
@login_required
def show_scoreboard():
    # Sort scoreboard by score descending
    sorted_scores = sorted(scoreboard, key=lambda x: x['score'], reverse=True)
    return render_template('scoreboard.html', scoreboard=sorted_scores)

@app.route('/my-activities')
@login_required
def my_activities_list():
    user_id = session.get('user_id')
    if user_id == 'organizer':
        return redirect(url_for('home'))
        
    user_events = [e for e in events if user_id in e['participants']]
    return render_template('my_activities.html', activities=user_events)

@app.route('/profile')
@login_required
def profile():
    user_id = session.get('user_id')
    current_user = users.get(user_id)
    return render_template('profile.html', user=current_user)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('base.html'), 404

if __name__ == '__main__':
    app.run(debug=True)
