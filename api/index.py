from flask import Flask, request, send_file
from pypdf import PdfReader, PdfWriter
import io

app = Flask(__name__)

# --- THE FIX: CATCH-ALL ROUTE ---
# This accepts POST requests on any URL path. 
# It prevents Vercel/Flask path mismatches.
@app.route('/', defaults={'path': ''}, methods=['POST', 'GET'])
@app.route('/<path:path>', methods=['POST', 'GET'])
def catch_all(path):
    # If someone visits the API URL directly in browser (GET), show a status message
    if request.method == 'GET':
        return "API is Running. Please use the form on the homepage to upload."

    # --- PROCESSING LOGIC (POST) ---
    try:
        if 'file' not in request.files:
            return "No file part", 400
        
        file = request.files['file']
        notes_input = request.form.get('notes', '')

        try:
            if notes_input.strip():
                note_pages = [int(x.strip()) for x in notes_input.split(',')]
            else:
                note_pages = []
        except ValueError:
            return "Invalid page numbers", 400

        input_stream = io.BytesIO(file.read())
        reader = PdfReader(input_stream)
        writer = PdfWriter()

        if len(reader.pages) > 0:
            ref_page = reader.pages[0]
            width = ref_page.mediabox.width
            height = ref_page.mediabox.height
        else:
            return "Empty PDF", 400

        total_input_pages = len(reader.pages)
        for i in range(total_input_pages):
            current_page_num = i + 1
            page = reader.pages[i]
            writer.add_page(page)
            
            if current_page_num not in note_pages:
                writer.add_blank_page(width=width, height=height)

        while len(writer.pages) % 4 != 0:
            writer.add_blank_page(width=width, height=height)

        output_stream = io.BytesIO()
        writer.write(output_stream)
        output_stream.seek(0)

        return send_file(
            output_stream,
            as_attachment=True,
            download_name='booklet_ready.pdf',
            mimetype='application/pdf'
        )
    except Exception as e:
        return f"Server Error: {str(e)}", 500

if __name__ == '__main__':
    app.run()
