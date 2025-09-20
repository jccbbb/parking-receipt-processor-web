from flask import Flask, render_template, request, send_file, jsonify, session
import os
import tempfile
import uuid
from pdf_processor import ParkingReceiptProcessor
from werkzeug.utils import secure_filename
import shutil

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

# Store processing status for progress tracking
processing_status = {}


@app.route('/')
def index():
    """Main page with upload form"""
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_pdf():
    """Handle PDF upload and initiate processing"""
    if 'pdf_file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['pdf_file']

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'File must be a PDF'}), 400

    # Generate unique session ID
    session_id = str(uuid.uuid4())

    # Save uploaded file
    filename = secure_filename(file.filename)
    input_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{session_id}_input.pdf")
    file.save(input_path)

    # Initialize processing status
    processing_status[session_id] = {
        'status': 'processing',
        'progress': 0,
        'total': 0,
        'message': 'Starting processing...'
    }

    try:
        # Process PDF
        processor = ParkingReceiptProcessor()

        def update_progress(current, total):
            processing_status[session_id]['progress'] = current
            processing_status[session_id]['total'] = total
            processing_status[session_id]['message'] = f'Processing page {current + 1} of {total}...'

        total_receipts, unique_receipts, total_amount = processor.process_pdf(
            input_path,
            progress_callback=update_progress
        )

        # Generate output PDF
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{session_id}_output.pdf")
        processing_status[session_id]['message'] = 'Generating output PDF...'

        success = processor.generate_output_pdf(input_path, output_path)

        if not success:
            raise Exception("Failed to generate output PDF")

        # Generate summary text
        summary_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{session_id}_summary.txt")
        processor.export_summary_text(summary_path)

        # Update status
        processing_status[session_id] = {
            'status': 'completed',
            'progress': 100,
            'total': 100,
            'message': 'Processing completed!',
            'summary': processor.get_summary(),
            'input_path': input_path,
            'output_path': output_path,
            'summary_path': summary_path
        }

        return jsonify({
            'session_id': session_id,
            'status': 'completed',
            'summary': processor.get_summary()
        })

    except Exception as e:
        processing_status[session_id] = {
            'status': 'error',
            'message': str(e)
        }
        # Clean up files on error
        if os.path.exists(input_path):
            os.remove(input_path)
        return jsonify({'error': str(e)}), 500


@app.route('/status/<session_id>')
def get_status(session_id):
    """Get processing status"""
    if session_id not in processing_status:
        return jsonify({'error': 'Session not found'}), 404

    return jsonify(processing_status[session_id])


@app.route('/download/<session_id>/<file_type>')
def download_file(session_id, file_type):
    """Download processed files"""
    if session_id not in processing_status:
        return jsonify({'error': 'Session not found'}), 404

    status = processing_status[session_id]

    if status['status'] != 'completed':
        return jsonify({'error': 'Processing not completed'}), 400

    if file_type == 'pdf':
        file_path = status['output_path']
        filename = 'processed_receipts.pdf'
        mimetype = 'application/pdf'
    elif file_type == 'summary':
        file_path = status['summary_path']
        filename = 'summary.txt'
        mimetype = 'text/plain'
    else:
        return jsonify({'error': 'Invalid file type'}), 400

    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404

    return send_file(
        file_path,
        as_attachment=True,
        download_name=filename,
        mimetype=mimetype
    )


@app.route('/cleanup/<session_id>', methods=['POST'])
def cleanup_session(session_id):
    """Clean up session files"""
    if session_id in processing_status:
        status = processing_status[session_id]

        # Remove files
        for key in ['input_path', 'output_path', 'summary_path']:
            if key in status and os.path.exists(status[key]):
                try:
                    os.remove(status[key])
                except:
                    pass

        # Remove from status
        del processing_status[session_id]

    return jsonify({'status': 'cleaned'})


@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file too large error"""
    return jsonify({'error': 'File too large. Maximum size is 100MB'}), 413


if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)

    # Run in production mode
    app.run(host='0.0.0.0', port=5000, debug=False)