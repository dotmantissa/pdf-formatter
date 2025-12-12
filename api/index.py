from flask import Flask, request, send_file
# strict import to ensure we are using the modern library
from pypdf import PdfReader, PdfWriter 
import io

app = Flask(__name__)

@app.route('/api/process', methods=['POST'])
def process_pdf():
    if 'file' not in request.files:
        return "No file part", 400
    
    file = request.files['file']
    notes_input = request.form.get('notes', '')

    # Parse note pages (comma separated string to list of integers)
    try:
        if notes_input.strip():
            note_pages = [int(x.strip()) for x in notes_input.split(',')]
        else:
            note_pages = []
    except ValueError:
        return "Invalid page numbers provided. Please use numbers separated by commas.", 400

    # Read the uploaded PDF from memory
    input_stream = io.BytesIO(file.read())
    reader = PdfReader(input_stream)
    writer = PdfWriter()

    # Get dimensions from the first page for consistent blank pages
    if len(reader.pages) > 0:
        ref_page = reader.pages[0]
        width = ref_page.mediabox.width
        height = ref_page.mediabox.height
    else:
        return "Empty PDF", 400

    # --- LOGIC: Add Blanks for Non-Note Pages ---
    total_input_pages = len(reader.pages)
    
    for i in range(total_input_pages):
        current_page_num = i + 1
        page = reader.pages[i]
        
        # Add the content page
        writer.add_page(page)
        
        # If it is NOT a note page, add a blank back
        if current_page_num not in note_pages:
            writer.add_blank_page(width=width, height=height)

    # --- LOGIC: Pad to Multiple of 4 (Booklet Standard) ---
    # Booklets must be multiples of 4 to fold correctly without loose sheets
    while len(writer.pages) % 4 != 0:
        writer.add_blank_page(width=width, height=height)

    # Save to memory buffer
    output_stream = io.BytesIO()
    writer.write(output_stream)
    output_stream.seek(0)

    return send_file(
        output_stream,
        as_attachment=True,
        download_name='booklet_ready.pdf',
        mimetype='application/pdf'
    )

# Vercel requires the app to be exposed as 'app'
if __name__ == '__main__':
    app.run(debug=True)
