import PyPDF2
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from PIL import Image
import os
import img2pdf
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

class MultiFileSelector:
    def __init__(self, title="Select Files to Merge"):
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry("600x500")
        
        # File type selection
        self.file_types = [
            ("PDF Files", "*.pdf"),
            ("Image Files", "*.jpg *.jpeg *.png *.gif *.bmp *.tiff"),
            ("All Supported Files", "*.pdf *.jpg *.jpeg *.png *.gif *.bmp *.tiff"),
            ("All Files", "*.*")
        ]
        
        # Selected files
        self.selected_files = []
        
        # Create UI
        self.create_widgets()
        
    def create_widgets(self):
        # File type dropdown
        tk.Label(self.root, text="Select File Type:").pack(pady=5)
        self.file_type_var = tk.StringVar()
        file_type_dropdown = ttk.Combobox(
            self.root, 
            textvariable=self.file_type_var, 
            values=[ft[0] for ft in self.file_types],
            state="readonly"
        )
        file_type_dropdown.pack(pady=5)
        file_type_dropdown.set(self.file_types[0][0])
        file_type_dropdown.bind("<<ComboboxSelected>>", self.load_files)
        
        # Scrollable file list with checkboxes
        self.file_frame = tk.Frame(self.root)
        self.file_frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        
        self.canvas = tk.Canvas(self.file_frame)
        scrollbar = ttk.Scrollbar(self.file_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Merge button
        merge_button = tk.Button(self.root, text="Merge Selected Files", command=self.merge_selected_files)
        merge_button.pack(pady=10)
        
    def load_files(self, event=None):
        # Clear previous checkboxes
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        # Get selected file type pattern
        selected_type = self.file_type_var.get()
        file_pattern = next(ft[1] for ft in self.file_types if ft[0] == selected_type)
        
        # Open file dialog
        file_paths = filedialog.askopenfilenames(
            title=f"Select {selected_type}", 
            filetypes=[(selected_type, file_pattern)]
        )
        
        # Create checkboxes for selected files
        self.file_vars = {}
        for file_path in file_paths:
            var = tk.BooleanVar(value=True)
            self.file_vars[file_path] = var
            cb = tk.Checkbutton(
                self.scrollable_frame, 
                text=os.path.basename(file_path), 
                variable=var
            )
            cb.pack(anchor='w')
        
    def merge_selected_files(self):
        # Get selected files
        self.selected_files = [
            file for file, var in self.file_vars.items() if var.get()
        ]
        
        # Validate selection
        if not self.selected_files:
            messagebox.showwarning("Warning", "No files selected.")
            return
        
        if len(self.selected_files) < 2:
            messagebox.showwarning("Warning", "Please select at least two files to merge.")
            return
        
        # Ask for output filename
        output_filename = simpledialog.askstring("Output", "Enter name for merged file:")
        if not output_filename:
            return
        
        # Merge files into PDF
        try:
            # Create a new PDF merger
            merger = PyPDF2.PdfMerger()
            
            # Convert each file to PDF
            for file_path in self.selected_files:
                file_ext = os.path.splitext(file_path)[1].lower()
                
                # PDF files can be directly added
                if file_ext == '.pdf':
                    merger.append(file_path)
                
                # Convert images to PDF
                elif file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']:
                    img = Image.open(file_path)
                    pdf_path = file_path.rsplit('.', 1)[0] + '_temp.pdf'
                    img.convert('RGB').save(pdf_path, 'PDF')
                    merger.append(pdf_path)
                    os.remove(pdf_path)  # Clean up temporary PDF
                
                # Convert other file types to PDF using img2pdf or reportlab
                else:
                    try:
                        # Try converting with img2pdf first
                        import img2pdf
                        with open(file_path, 'rb') as file:
                            pdf_bytes = img2pdf.convert(file)
                            pdf_path = file_path.rsplit('.', 1)[0] + '_temp.pdf'
                            with open(pdf_path, 'wb') as pdf_file:
                                pdf_file.write(pdf_bytes)
                            merger.append(pdf_path)
                            os.remove(pdf_path)  # Clean up temporary PDF
                    except ImportError:
                        # Fallback to reportlab if img2pdf is not available
                        from reportlab.pdfgen import canvas
                        from reportlab.lib.pagesizes import letter
                        
                        pdf_path = file_path.rsplit('.', 1)[0] + '_temp.pdf'
                        c = canvas.Canvas(pdf_path, pagesize=letter)
                        width, height = letter
                        
                        # Add file content to PDF (basic conversion)
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                            text = file.read()
                            text_object = c.beginText(100, height - 100)
                            text_object.setFont("Helvetica", 12)
                            
                            # Split text into lines
                            for line in text.split('\n'):
                                text_object.textLine(line)
                            
                            c.drawText(text_object)
                            c.showPage()
                            c.save()
                        
                        merger.append(pdf_path)
                        os.remove(pdf_path)  # Clean up temporary PDF
            
            # Write the merged PDF
            output_filename += ".pdf"
            merger.write(output_filename)
            merger.close()
            
            messagebox.showinfo("Success", f"Merged PDF saved as: {output_filename}")
        
        except Exception as e:
            messagebox.showerror("Error", f"Merge failed: {str(e)}")
        
        # Close the window
        self.root.destroy()
    
    def run(self):
        self.root.mainloop()

def merge_files():
    app = MultiFileSelector()
    app.run()

if __name__ == "__main__":
    merge_files()
