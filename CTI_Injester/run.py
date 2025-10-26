#!/usr/bin/env python3
"""
OpenCTI Injester - GitHub-based Data Collector
Main application with plugin architecture for TOR and MalwareBazaar data collection
"""

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_session import Session
import os
import importlib.util
from pathlib import Path
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import json

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './flask_session'
Session(app)

# Disable caching
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['TEMPLATES_AUTO_RELOAD'] = True

@app.after_request
def after_request(response):
    """Add headers to prevent caching."""
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# Global scheduler for all plugins
scheduler = BackgroundScheduler(daemon=True)
plugins = []

def load_plugins():
    """Load all plugins from the plugin directory"""
    global plugins
    plugins = []
    plugin_dir = Path(__file__).parent / 'plugin'

    logger.info(f"Loading plugins from: {plugin_dir}")
    if not plugin_dir.exists():
        plugin_dir.mkdir(parents=True)
        logger.info("Created plugin directory")
        return

    for plugin_folder in sorted(plugin_dir.iterdir()):
        if plugin_folder.is_dir() and not plugin_folder.name.startswith('__'):
            plugin_main = plugin_folder / 'main.py'

            if plugin_main.exists():
                logger.info(f"Loading plugin: {plugin_folder.name}")
                try:
                    spec = importlib.util.spec_from_file_location(
                        f"plugin.{plugin_folder.name}",
                        plugin_main
                    )

                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)

                        if hasattr(module, 'create_blueprint'):
                            blueprint = module.create_blueprint()
                            app.register_blueprint(
                                blueprint,
                                url_prefix=f'/plugin/{plugin_folder.name}'
                            )

                            # Initialize plugin scheduler if available
                            if hasattr(module, 'initialize_scheduler'):
                                module.initialize_scheduler(scheduler)

                            plugin_info = {
                                'name': getattr(module, 'PLUGIN_NAME', plugin_folder.name),
                                'description': getattr(module, 'PLUGIN_DESCRIPTION', ''),
                                'url_prefix': f'/plugin/{plugin_folder.name}',
                                'folder': plugin_folder.name,
                                'module': module
                            }
                            plugins.append(plugin_info)
                            logger.info(f"Successfully loaded plugin: {plugin_info['name']}")
                        else:
                            logger.warning(f"Plugin {plugin_folder.name} missing create_blueprint function")
                except Exception as e:
                    logger.error(f"Error loading plugin {plugin_folder.name}: {str(e)}", exc_info=True)

@app.route('/')
def index():
    """Main page showing all plugins"""
    if not session.get('authenticated'):
        return redirect(url_for('login'))
    return render_template('index.html', plugins=plugins)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Simple authentication page"""
    session['authenticated'] = True
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    """Logout and clear session"""
    session.clear()
    return redirect(url_for('login'))

@app.route('/api/scheduler/status')
def scheduler_status():
    """Get scheduler status and jobs"""
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            'id': job.id,
            'name': job.name,
            'next_run': str(job.next_run_time) if job.next_run_time else 'Not scheduled',
            'trigger': str(job.trigger)
        })
    return jsonify({
        'running': scheduler.running,
        'jobs': jobs,
        'current_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    return {'status': 'healthy', 'plugins_loaded': len(plugins)}, 200

# Load plugins on startup
load_plugins()

# Start scheduler
scheduler.start()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5055)