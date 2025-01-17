from flask import Flask, request, jsonify
from models import db, Log
from datetime import datetime, timedelta

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost:3306/activity_logs'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()


@app.route('/logs', methods=['POST'])
def add_log():
    data = request.get_json()
    if not data or 'user_id' not in data or 'activity' not in data:
        return jsonify({'error': 'Missing required fields'}), 400

    log = Log(
        user_id=data['user_id'],
        activity=data['activity'],
        timestamp=datetime.fromisoformat(data.get('timestamp', datetime.utcnow().isoformat())),
        meta_data=data.get('metadata', {})
    )
    db.session.add(log)
    db.session.commit()
    return jsonify({'message': 'Log added successfully', 'log': {
        'user_id': log.user_id,
        'activity': log.activity,
        'timestamp': log.timestamp.isoformat(),
        'meta_data': log.meta_data
    }}), 201


@app.route('/logs/<user_id>', methods=['GET'])
def get_user_logs(user_id):
    start_date = datetime.utcnow() - timedelta(days=7)
    end_date = datetime.utcnow()

    activity_filter = 'login'

    query = Log.query.filter(
        Log.user_id == user_id,
        Log.activity == activity_filter,
        Log.timestamp >= start_date,
        Log.timestamp <= end_date
    )

    logs = query.all()

    return jsonify([{
        'user_id': log.user_id,
        'activity': log.activity,
        'timestamp': log.timestamp.isoformat(),
        'meta_data': log.meta_data
    } for log in logs]), 200


@app.route('/logs/stats', methods=['GET'])
def get_logs_stats():
    start_date = request.args.get('start', (datetime.utcnow() - timedelta(days=7)).isoformat())
    end_date = request.args.get('end', datetime.utcnow().isoformat())

    try:
        start_date = datetime.fromisoformat(start_date)
        end_date = datetime.fromisoformat(end_date)
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

    user_activity_count = db.session.query(
        Log.user_id, db.func.count(Log.user_id).label('activity_count')
    ).filter(
        Log.timestamp >= start_date,
        Log.timestamp <= end_date
    ).group_by(Log.user_id).all()

    most_frequent_activity = db.session.query(
        Log.activity, db.func.count(Log.user_id).label('count')
    ).filter(
        Log.timestamp >= start_date,
        Log.timestamp <= end_date
    ).group_by(Log.activity).order_by(db.desc('count')).first()

    # Prepare results
    user_activity_count_dict = {user_id: count for user_id, count in user_activity_count}
    most_frequent_activity_name = most_frequent_activity.activity if most_frequent_activity else None

    return jsonify({
        'user_activity_count': user_activity_count_dict,
        'most_frequent_activity': most_frequent_activity_name
    }), 200


@app.route('/logs/<int:user_id>', methods=['PUT'])
def update_log(user_id):
    data = request.get_json()
    log = Log.query.get(user_id)

    if not log:
        return jsonify({'error': 'Log not found'}), 404

    if 'activity' in data:
        log.activity = data['activity']

    db.session.commit()

    return jsonify({'message': 'Log updated successfully', 'log': {
        'user_id': log.user_id,
        'activity': log.activity,
        'timestamp': log.timestamp.isoformat(),
        'meta_data': log.meta_data
    }}), 200


# Error handling
@app.errorhandler(404)
def resource_not_found(e):
    return jsonify({'error': 'Resource not found'}), 404


if __name__ == '__main__':
    app.run(debug=True)

