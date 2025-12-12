from flask import Flask, request, send_file
from pypdf import PdfReader, PdfWriter
import io

app = Flask(__name__)

# Note: Because this file is named 'process.py', Vercel routes 
# requests from /api/process directly here. 
# We use route('/') because inside this file, it is the root.
@app.route('/', methods=['POST'])
def process_pdf():
    try:
        if 'file' not in request.files:
            return "No file part", 400
        
        file = request.files['file']
        notes_input = request.form.get('notes', '')

        # Parse note pages
        try:
            if notes_input.strip():
                note_pages = [int(x.strip()) for x in notes_input.split(',')]
            else:
                note_pages = []
        except ValueError:
            return "Invalid page numbers. Use 1, 3, 5...", 400

        input_stream = io.BytesIO(file.read())
        reader = PdfReader(input_stream)
        writer = PdfWriter()

        if len(reader.pages) > 0:
            ref_page = reader.pages[0]
            width = ref_page.mediabox.width
            height = ref_page.mediabox.height
        else:
            return "Empty PDF", 400

        # --- LOGIC ---
        total_input_pages = len(reader.pages)
        for i in range(total_input_pages):
            current_page_num = i + 1
            page = reader.pages[i]
            writer.add_page(page)
            
            # Logic: If NOT a note page, add blank back
            if current_page_num not in note_pages:
                writer.add_blank_page(width=width, height=height)

        # Pad to multiple of 4
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

# Required for Vercel
if __name__ == '__main__':
    app.run()
