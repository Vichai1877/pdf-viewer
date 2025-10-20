import io
import tkinter as tk
from dataclasses import dataclass
from enum import Enum
from tkinter import filedialog, messagebox, ttk
from typing import List, Optional, Tuple

import fitz  # PyMuPDF
from PIL import Image, ImageTk

# convert point in pdf to mm for Reportlab
def pt2mm( pt : float =0 ) -> float :
    return pt* 25.4 / 72

class OriginPoint(Enum):
    """Enumeration for coordinate origin points."""
    TOP_LEFT = "Top-Left"
    TOP_RIGHT = "Top-Right"
    BOTTOM_LEFT = "Bottom-Left"
    BOTTOM_RIGHT = "Bottom-Right"

@dataclass
class DocumentPart(Enum):
    """Enumeration for document part."""
    HEADING = "Heading"
    BODY = "Body"
    SUMMARY = "Summary"
    LINESPACE = "Linespace"  # for set line spacing by put line spacing to Raw_Y ใช้กำหนด ระยะ spacing โดยส่งค่าไปที่ "Raw_Y"

@dataclass
class DataTypes(Enum):
    """Enumeration for document type."""
    TEXT = "Text"
    NUMBER0 = "Numeric"
    NUMBER2 = "Numeric 2 digits"
    DATE = "Date"
    IMAGE = "Image"
    VIDEO = "Video"
    AUDIO = "Audio"

class Alignments(Enum):
    """Enumeration for alignment type."""
    LEFT = "Left"
    RIGHT = "Right"
    CENTER = "Center"

@dataclass
class ClickData:
    """Data class to store click information."""
    page_number: int
    raw_x: float
    raw_y: float
    adjusted_x: float
    adjusted_y: float
    origin: OriginPoint
    part : DocumentPart
    name: str       # name of point
    mm_x : float    # Millimeter unit (mm)
    mm_y : float    # Millimeter unit (mm)
    datatype : DataTypes    # type of data
    alignment : Alignments  # alingment

class CoordinateTransformer:
    """Handles coordinate transformations between different origin points."""

    @staticmethod
    def adjust_coordinates(
        raw_x: float, raw_y: float, page_width: float, page_height: float, origin: OriginPoint
    ) -> Tuple[float, float]:
        """
        Convert coordinates from PyMuPDF's default (top-left) to user-selected origin.

        Args:
            raw_x, raw_y: Original coordinates from PyMuPDF (top-left origin)
            page_width, page_height: Dimensions of the PDF page
            origin: Target origin point

        Returns:
            Tuple of adjusted (x, y) coordinates
        """
        if origin == OriginPoint.TOP_LEFT:
            return raw_x, raw_y
        elif origin == OriginPoint.TOP_RIGHT:
            return page_width - raw_x, raw_y
        elif origin == OriginPoint.BOTTOM_LEFT:
            return raw_x, page_height - raw_y
        elif origin == OriginPoint.BOTTOM_RIGHT:
            return page_width - raw_x, page_height - raw_y
        else:
            raise ValueError(f"Unknown origin point: {origin}")


class PDFViewer:
    """Main PDF viewer application class."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("PDF Coordinate Viewer")
        # Set a reasonable default size, will be adjusted in main()
        self.root.geometry("1200x800")

        # PDF-related attributes
        self.pdf_document: Optional[fitz.Document] = None
        self.current_page_number = 0
        self.total_pages = 0
        self.current_page_pixmap = None
        self.page_width = 0
        self.page_height = 0

        # UI state
        self.selected_origin = tk.StringVar(value=OriginPoint.BOTTOM_LEFT.value)
        self.click_history: List[ClickData] = []
        self.click_markers: List[int] = []  # Canvas item IDs for markers

        # Drag state
        self.dragging_point = None
        self.drag_data = {"x": 0, "y": 0, "point_index": -1}

        # Zoom and display
        self.zoom_factor = 1.0
        self.canvas_width = 800
        self.canvas_height = 600

        self.setup_ui()
        self.setup_bindings()

    def setup_ui(self):
        """Create and layout the user interface components."""
        # Create menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open PDF...", command=self.open_pdf, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="Import Click History...", command=self.import_history, accelerator="Ctrl+I")
        file_menu.add_command(label="Export Click History...", command=self.export_history, accelerator="Ctrl+E")
        file_menu.add_separator()
        file_menu.add_command(label="Edit Selected Point...", command=self.edit_selected_point, accelerator="F2")
        file_menu.add_command(label="Delete Selected Point", command=self.delete_selected_point, accelerator="Del")
        file_menu.add_command(label="Clear History", command=self.clear_history)

        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Top control panel
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))

        # File operations
        file_frame = ttk.LabelFrame(control_frame, text="File")
        file_frame.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(file_frame, text="Open PDF", command=self.open_pdf).pack(side=tk.LEFT, padx=5, pady=5)

        # Page navigation
        nav_frame = ttk.LabelFrame(control_frame, text="Navigation")
        nav_frame.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(nav_frame, text="◀ Previous", command=self.previous_page).pack(side=tk.LEFT, padx=2, pady=5)

        self.page_label = ttk.Label(nav_frame, text="No PDF loaded")
        self.page_label.pack(side=tk.LEFT, padx=10, pady=5)

        ttk.Button(nav_frame, text="Next ▶", command=self.next_page).pack(side=tk.LEFT, padx=2, pady=5)

        # Origin selection
        origin_frame = ttk.LabelFrame(control_frame, text="Coordinate Origin")
        origin_frame.pack(side=tk.LEFT, padx=(0, 10))

        origin_combo = ttk.Combobox(
            origin_frame,
            textvariable=self.selected_origin,
            values=[origin.value for origin in OriginPoint],
            state="readonly",
            width=15,
        )
        origin_combo.pack(padx=5, pady=5)
        origin_combo.bind("<<ComboboxSelected>>", self.on_origin_changed)

        # Zoom controls
        zoom_frame = ttk.LabelFrame(control_frame, text="Zoom")
        zoom_frame.pack(side=tk.LEFT)

        ttk.Button(zoom_frame, text="Zoom In", command=self.zoom_in).pack(side=tk.LEFT, padx=2, pady=5)
        ttk.Button(zoom_frame, text="Zoom Out", command=self.zoom_out).pack(side=tk.LEFT, padx=2, pady=5)
        ttk.Button(zoom_frame, text="Reset", command=self.reset_zoom).pack(side=tk.LEFT, padx=2, pady=5)

        # Main content area
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # PDF display area with scrollbars
        canvas_frame = ttk.Frame(content_frame)
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # Create canvas with scrollbars
        self.canvas = tk.Canvas(canvas_frame, bg="white", width=self.canvas_width, height=self.canvas_height)

        v_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        h_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)

        self.canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # Grid layout for canvas and scrollbars
        self.canvas.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")

        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)

        # Right panel for coordinates and history
        right_panel = ttk.Frame(content_frame, width=350)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y)
        right_panel.pack_propagate(False)

        # Current click info
        current_frame = ttk.LabelFrame(right_panel, text="Current Click")
        current_frame.pack(fill=tk.X, pady=(0, 10))

        self.current_coords_label = ttk.Label(
            current_frame, text="Click on PDF to see coordinates", wraplength=280, justify=tk.LEFT
        )
        self.current_coords_label.pack(padx=10, pady=10)

        # Click history
        history_frame = ttk.LabelFrame(right_panel, text="Click History")
        history_frame.pack(fill=tk.BOTH, expand=True)

        # History listbox with scrollbar
        history_list_frame = ttk.Frame(history_frame)
        history_list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.history_listbox = tk.Listbox(history_list_frame, font=("Helvetica", 11))
        history_scrollbar = ttk.Scrollbar(history_list_frame, orient=tk.VERTICAL, command=self.history_listbox.yview)
        self.history_listbox.configure(yscrollcommand=history_scrollbar.set)

        # Add double-click binding for editing
        self.history_listbox.bind("<Double-Button-1>", lambda e: self.edit_selected_point())

        self.history_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        history_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # History controls
        history_controls = ttk.Frame(history_frame)
        history_controls.pack(fill=tk.X, padx=5, pady=(0, 5))

        ttk.Button(history_controls, text="Clear History", command=self.clear_history).grid(row=0,column=0)
        ttk.Button(history_controls, text="Edit Point", command=self.edit_selected_point).grid(row=0,column=1)
        ttk.Button(history_controls, text="Delete Point", command=self.delete_selected_point).grid(row=0,column=2)

        ttk.Button(history_controls, text="Import CSV", command=self.import_history).grid(row=1,column=0)
        ttk.Button(history_controls, text="Export CSV", command=self.export_history).grid(row=1,column=1)

    def setup_bindings(self):
        """Set up event bindings."""
        self.root.bind("<KeyPress-Left>", lambda e: self.previous_page())
        self.root.bind("<KeyPress-Right>", lambda e: self.next_page())
        self.root.bind("<Control-o>", lambda e: self.open_pdf())
        self.root.bind("<Control-e>", lambda e: self.export_history())
        self.root.bind("<Control-i>", lambda e: self.import_history())
        self.root.bind("<F2>", lambda e: self.edit_selected_point())
        self.root.bind("<Delete>", lambda e: self.delete_selected_point())

        # Mouse wheel scrolling
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)
        self.canvas.bind("<Button-4>", self.on_mousewheel)  # Linux
        self.canvas.bind("<Button-5>", self.on_mousewheel)  # Linux

        # Horizontal scrolling with Shift+MouseWheel
        self.canvas.bind("<Shift-MouseWheel>", self.on_horizontal_mousewheel)
        self.canvas.bind("<Shift-Button-4>", self.on_horizontal_mousewheel)  # Linux
        self.canvas.bind("<Shift-Button-5>", self.on_horizontal_mousewheel)  # Linux

        # Canvas click and focus handling
        self.canvas.bind("<Enter>", lambda e: self.canvas.focus_set())

        # Drag functionality for markers (also handles regular clicks)
        self.canvas.bind("<ButtonPress-1>", self.on_marker_press)
        self.canvas.bind("<B1-Motion>", self.on_marker_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_marker_release)

    def on_mousewheel(self, event):
        """Handle vertical mouse wheel scrolling."""
        if not self.pdf_document:
            return

        # Check if there's content to scroll
        bbox = self.canvas.bbox("all")
        if not bbox or self.canvas.winfo_height() >= bbox[3]:
            return  # No need to scroll if content fits in view

        # Determine scroll direction and amount
        if event.num == 4 or event.delta > 0:
            # Scroll up
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0:
            # Scroll down
            self.canvas.yview_scroll(1, "units")

    def on_horizontal_mousewheel(self, event):
        """Handle horizontal mouse wheel scrolling (with Shift)."""
        if not self.pdf_document:
            return

        # Check if there's content to scroll
        bbox = self.canvas.bbox("all")
        if not bbox or self.canvas.winfo_width() >= bbox[2]:
            return  # No need to scroll if content fits in view

        # Determine scroll direction and amount
        if event.num == 4 or event.delta > 0:
            # Scroll left
            self.canvas.xview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0:
            # Scroll right
            self.canvas.xview_scroll(1, "units")

    def open_pdf(self):
        """Open and load a PDF file."""
        file_path = filedialog.askopenfilename(
            title="Select PDF file", filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )

        if not file_path:
            return

        try:
            # Close previous document if any
            if self.pdf_document:
                self.pdf_document.close()

            # Open new document
            self.pdf_document = fitz.open(file_path)
            self.total_pages = len(self.pdf_document)
            self.current_page_number = 0

            # Clear previous state
            self.clear_canvas()
            self.clear_history()

            # Load first page
            self.load_page()

            # Update UI
            self.update_page_label()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to open PDF: {str(e)}")

    def load_page(self):
        """Load and display the current page."""
        if not self.pdf_document or self.current_page_number >= self.total_pages:
            return

        try:
            # Get the page
            page = self.pdf_document[self.current_page_number]

            # Get page dimensions
            rect = page.rect
            self.page_width = rect.width
            self.page_height = rect.height

            # Create pixmap with zoom
            matrix = fitz.Matrix(self.zoom_factor, self.zoom_factor)
            self.current_page_pixmap = page.get_pixmap(matrix=matrix)

            # Convert to PIL Image
            img_data = self.current_page_pixmap.tobytes("ppm")
            pil_image = Image.open(io.BytesIO(img_data))

            # Convert to PhotoImage for Tkinter
            self.photo_image = ImageTk.PhotoImage(pil_image)

            # Clear canvas and display image
            self.clear_canvas()
            self.canvas_image_id = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo_image)

            # Update scroll region
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))

            # Redraw markers for current page
            self.redraw_markers()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load page: {str(e)}")

    def clear_canvas(self):
        """Clear the canvas."""
        self.canvas.delete("all")
        self.click_markers.clear()

    def on_canvas_click(self, event):
        """Handle mouse clicks on the PDF canvas."""
        if not self.pdf_document or not self.current_page_pixmap:
            return

        # Get canvas coordinates
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)

        # Convert to PDF coordinates (accounting for zoom)
        pdf_x = canvas_x / self.zoom_factor
        pdf_y = canvas_y / self.zoom_factor

        # Get selected origin
        origin = OriginPoint(self.selected_origin.get())

        # Transform coordinates
        adjusted_x, adjusted_y = CoordinateTransformer.adjust_coordinates(
            pdf_x, pdf_y, self.page_width, self.page_height, origin
        )

        # Create click data
        click_data = ClickData(
            page_number=self.current_page_number + 1,  # 1-based for display
            raw_x=pdf_x,
            raw_y=pdf_y,
            adjusted_x=adjusted_x,
            adjusted_y=adjusted_y,
            origin=origin,
            part=DocumentPart.HEADING.value,
            name=f"point_{len(self.click_history)+1}",  # not
            mm_x= pt2mm(adjusted_x),
            mm_y= pt2mm(adjusted_y),
            datatype=DataTypes.TEXT.value,
            alignment=Alignments.LEFT.value,
        )

        # Add to history
        self.click_history.append(click_data)

        # Update displays
        self.update_current_coords_display(click_data)
        self.update_history_listbox()

        # Add visual marker with number
        click_number = len(self.click_history)
        self.add_click_marker(canvas_x, canvas_y, click_number)

    def add_click_marker(self, canvas_x: float, canvas_y: float, number: Optional[int] = None):
        """Add a visual marker at the clicked position."""
        # Create a small circle marker
        marker_size = 5
        marker_id = self.canvas.create_oval(
            canvas_x - marker_size,
            canvas_y - marker_size,
            canvas_x + marker_size,
            canvas_y + marker_size,
            fill="red",
            outline="darkred",
            width=2,
        )
        self.click_markers.append(marker_id)

        # Also add a small cross for precision
        cross_size = 8
        cross_id1 = self.canvas.create_line(
            canvas_x - cross_size, canvas_y, canvas_x + cross_size, canvas_y, fill="black", width=1
        )
        cross_id2 = self.canvas.create_line(
            canvas_x, canvas_y - cross_size, canvas_x, canvas_y + cross_size, fill="black", width=1
        )
        self.click_markers.extend([cross_id1, cross_id2])

        # Add number label if provided
        if number is not None:
            text_id = self.canvas.create_text(
                canvas_x + 12, canvas_y - 12, text=str(number), fill="blue", font=("Arial", 10, "bold"), anchor="nw"
            )
            self.click_markers.append(text_id)

    def clear_all_markers(self):
        """Remove all visual markers from the canvas."""
        # Delete all marker canvas items
        for marker_id in self.click_markers:
            self.canvas.delete(marker_id)
        # Clear the markers list
        self.click_markers.clear()

    def redraw_markers(self):
        """Redraw click markers for the current page."""
        # First, remove all existing markers
        self.clear_all_markers()

        # Then redraw markers for the current page based on history
        for i, click_data in enumerate(self.click_history):
            if click_data.page_number == self.current_page_number + 1:
                # Convert back to canvas coordinates
                canvas_x = click_data.raw_x * self.zoom_factor
                canvas_y = click_data.raw_y * self.zoom_factor
                # Use the original click number (i + 1)
                self.add_click_marker(canvas_x, canvas_y, i + 1)

    def update_current_coords_display(self, click_data: ClickData):
        """Update the current coordinates display."""
        text = f"Page: {click_data.page_number}\n"
        text += f"Origin: {click_data.origin.value}\n\n"
        text += "Raw coordinates (Top-Left):\n"
        text += f"X: {click_data.raw_x:.2f}\n"
        text += f"Y: {click_data.raw_y:.2f}\n\n"
        text += "Adjusted coordinates:\n"
        text += f"X: {click_data.adjusted_x:.2f}\n"
        text += f"Y: {click_data.adjusted_y:.2f}"

        self.current_coords_label.config(text=text)

    def update_history_listbox(self):
        """Update the history listbox."""
        self.history_listbox.delete(0, tk.END)

        for i, click_data in enumerate(self.click_history):
            entry = f"#{i + 1:2d} P{click_data.page_number} ({click_data.adjusted_x:.1f}, {click_data.adjusted_y:.1f}) {click_data.name} {click_data.part}"
            self.history_listbox.insert(tk.END, entry)

        # Auto-scroll to bottom
        self.history_listbox.see(tk.END)

    def on_origin_changed(self, event=None):
        """Handle origin selection change."""
        # Recalculate all coordinates in history
        origin = OriginPoint(self.selected_origin.get())

        for click_data in self.click_history:
            click_data.adjusted_x, click_data.adjusted_y = CoordinateTransformer.adjust_coordinates(
                click_data.raw_x, click_data.raw_y, self.page_width, self.page_height, origin
            )
            click_data.origin = origin

        # Update displays
        if self.click_history:
            self.update_current_coords_display(self.click_history[-1])
        self.update_history_listbox()

    def next_page(self):
        """Navigate to the next page."""
        if self.pdf_document and self.current_page_number < self.total_pages - 1:
            self.current_page_number += 1
            self.load_page()
            self.update_page_label()

    def previous_page(self):
        """Navigate to the previous page."""
        if self.pdf_document and self.current_page_number > 0:
            self.current_page_number -= 1
            self.load_page()
            self.update_page_label()

    def update_page_label(self):
        """Update the page number label."""
        if self.pdf_document:
            text = f"Page {self.current_page_number + 1} of {self.total_pages}"
        else:
            text = "No PDF loaded"
        self.page_label.config(text=text)

    def zoom_in(self):
        """Increase zoom level."""
        self.zoom_factor = min(self.zoom_factor * 1.25, 5.0)
        self.load_page()

    def zoom_out(self):
        """Decrease zoom level."""
        self.zoom_factor = max(self.zoom_factor / 1.25, 0.2)
        self.load_page()

    def reset_zoom(self):
        """Reset zoom to 100%."""
        self.zoom_factor = 1.0
        self.load_page()

    def clear_history(self):
        """Clear the click history and remove all visual markers."""
        self.click_history.clear()
        self.history_listbox.delete(0, tk.END)
        self.current_coords_label.config(text="Click on PDF to see coordinates")
        # Remove all visual markers from canvas
        self.clear_all_markers()

    def export_history(self):
        """Export click history to CSV file."""
        if not self.click_history:
            messagebox.showwarning("Warning", "No click history to export.")
            return

        file_path = filedialog.asksaveasfilename(
            title="Export Click History",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )

        if not file_path:
            return

        try:
            with open(file_path, "w", newline="",encoding="UTF-8") as csvfile:
                csvfile.write("Page,Origin,Raw_X,Raw_Y,X,Y,PART,NAME,MM_X,MM_Y,Data_Type,Align\n")
                for click_data in self.click_history:
                    csvfile.write(
                        f"{click_data.page_number},{click_data.origin.value},"
                        f"{click_data.raw_x:.2f},{click_data.raw_y:.2f},"
                        f"{click_data.adjusted_x:.2f},{click_data.adjusted_y:.2f},"
                        f"{click_data.part},"
                        f"{click_data.name},"
                        f"{click_data.mm_x:.2f},{click_data.mm_y:.2f},"
                        f"{click_data.datatype},"
                        f"{click_data.alignment}\n"
                    )

            messagebox.showinfo("Success", f"Click history exported to {file_path}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to export history: {str(e)}")

    def import_history(self):
        """Import click history from CSV file."""
        file_path = filedialog.askopenfilename(
            title="Import Click History",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )

        if not file_path:
            return

        try:
            imported_clicks = []
            with open(file_path, "r") as csvfile:
                lines = csvfile.readlines()

                # Skip header line if present
                start_line = 1 if lines and "Page" in lines[0] else 0

                for line_num, line in enumerate(lines[start_line:], start_line + 1):
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        parts = line.split(",")
                        if len(parts) != 12:
                            messagebox.showwarning(
                                "Warning", f"Line {line_num}: Invalid format, expected 12 columns, got {len(parts)}"
                            )
                            continue

                        page_number = int(parts[0])
                        origin_value = parts[1]
                        raw_x = float(parts[2])
                        raw_y = float(parts[3])
                        adjusted_x = float(parts[4])
                        adjusted_y = float(parts[5])
                        part = parts[6]
                        name = parts[7]
                        mm_x = float(parts[8])
                        mm_y = float(parts[9])
                        datatype = parts[10]
                        alignment = parts[11]

                        # Validate origin
                        try:
                            origin = OriginPoint(origin_value)
                        except ValueError:
                            messagebox.showwarning(
                                "Warning", f"Line {line_num}: Invalid origin '{origin_value}', skipping"
                            )
                            continue

                        click_data = ClickData(
                            page_number=page_number,
                            raw_x=raw_x,
                            raw_y=raw_y,
                            adjusted_x=adjusted_x,
                            adjusted_y=adjusted_y,
                            origin=origin,
                            part=part,
                            name=name,
                            mm_x=mm_x,
                            mm_y=mm_y,
                            datatype=datatype,
                            alignment=alignment
                        )
                        imported_clicks.append(click_data)

                    except (ValueError, IndexError) as e:
                        messagebox.showwarning("Warning", f"Line {line_num}: Invalid data format - {str(e)}")
                        continue

            if not imported_clicks:
                messagebox.showwarning("Warning", "No valid click data found in file.")
                return

            # Ask user if they want to replace or append
            result = messagebox.askyesnocancel(
                "Import Options",
                f"Found {len(imported_clicks)} click points.\n\n"
                "Yes: Replace current history\n"
                "No: Add to current history\n"
                "Cancel: Cancel import",
            )

            if result is None:  # Cancel
                return
            elif result:  # Yes - Replace
                self.click_history.clear()
                self.clear_all_markers()
            # else: No - Append (do nothing, just add to existing)

            # Add imported clicks to history
            self.click_history.extend(imported_clicks)

            # Update displays
            self.update_history_listbox()
            if self.click_history:
                self.update_current_coords_display(self.click_history[-1])

            # Redraw markers for current page
            if self.pdf_document:
                self.redraw_markers()

            messagebox.showinfo("Success", f"Successfully imported {len(imported_clicks)} click points!")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to import history: {str(e)}")

    def edit_selected_point(self):
        """Edit the coordinates of the selected point from history."""
        selection = self.history_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a point from the history list to edit.")
            return

        selected_index = selection[0]
        if selected_index >= len(self.click_history):
            messagebox.showerror("Error", "Invalid selection.")
            return

        click_data = self.click_history[selected_index]

        # Create edit dialog
        self.show_edit_coordinate_dialog(click_data, selected_index)

    def show_edit_coordinate_dialog(self, click_data: ClickData, index: int):
        """Show dialog to edit coordinate values."""
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Edit Point #{index + 1}")
        dialog.geometry("450x600")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        # Main frame with padding
        main_frame = ttk.Frame(dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # Point info section
        info_frame = ttk.LabelFrame(main_frame, text="Point Information", padding=10)
        info_frame.pack(fill=tk.X, pady=(0, 15))

        info_text = (
            f"Point Number: #{index + 1}\nPage: {click_data.page_number}\nCurrent Origin: {click_data.origin.value}"
        )
        ttk.Label(info_frame, text=info_text, justify=tk.LEFT).pack(anchor=tk.W)

        # Coordinate editing section
        coord_frame = ttk.LabelFrame(main_frame, text="Edit Coordinates", padding=10)
        coord_frame.pack(fill=tk.X, pady=(0, 15))
        # Name of point
        name_doc_frame = ttk.Frame(coord_frame)  # frame to contain point name and document part
        name_doc_frame.pack(fill=tk.X, pady=(0, 15))
        point_name_label = ttk.Label(name_doc_frame, text="Name of Point",font=("Arial", 9, "bold"))
        point_name_label.grid(column=0,row=0,sticky="W",pady=(0,5))
        point_name_var = tk.StringVar(value=click_data.name)
        point_name_label = ttk.Entry(name_doc_frame,textvariable=point_name_var,width=30)
        point_name_label.grid(column=0,row=1,pady=(0,5))
        # Document-Part editing section
        docpart_var = tk.StringVar()
        docpart_label = ttk.Label(name_doc_frame, text="Document Part", font=("Arial", 9, "bold"))
        docpart_label.grid(column=1,row=0,padx=6, pady=(0, 5),sticky="W")
        docpart_cbx = ttk.Combobox(
            name_doc_frame,
            textvariable=docpart_var,
            values=[doc.value for doc in DocumentPart],
            width=15
        )
        docpart_var.set(click_data.part)
        docpart_cbx.grid(column=1,row=1,padx=6, pady=(0,5),sticky="W")
        # frame for Type of data and alingment
        type_align_frame = ttk.Frame(coord_frame) # frame to contain type and aling combobox
        type_align_frame.pack(fill=tk.X, pady=(0, 15))
        # Type of data
        datatype_label = ttk.Label(type_align_frame,text="Data Type",font=("Arial", 9, "bold"))
        datatype_label.grid(column=0,row=0,sticky="W",pady=(0,5))
        datatype_var = tk.StringVar()
        datatype_cbx = ttk.Combobox(
            type_align_frame,
            textvariable=datatype_var,
            values=[t.value for t in DataTypes],
            width=21
        )
        datatype_var.set(click_data.datatype)
        datatype_cbx.grid(column=0,row=1,padx=(0,6), pady=(0,5),sticky="W")
        # Alignment
        align_label = ttk.Label(type_align_frame,text="Alignment",font=("Arial", 9, "bold"))
        align_label.grid(column=1,row=0,sticky="W",pady=(0,5))
        align_var = tk.StringVar(value=click_data.alignment)
        align_cbx = ttk.Combobox(
            type_align_frame,
            textvariable=align_var,
            values=[a.value for a in Alignments],
            width=21
        )
        align_var.set(click_data.alignment)
        align_cbx.grid(column=1,row=1,padx=(6,0), pady=(0,5),sticky="W")

        # Raw coordinates section
        raw_label = ttk.Label(coord_frame, text="Raw Coordinates (Top-Left):", font=("Arial", 9, "bold"))
        raw_label.pack(anchor=tk.W, pady=(0, 5))

        raw_container = ttk.Frame(coord_frame)
        raw_container.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(raw_container, text="X:", width=2).grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        raw_x_var = tk.StringVar(value=f"{click_data.raw_x:.2f}")
        raw_x_entry = ttk.Entry(raw_container, textvariable=raw_x_var, width=15)
        raw_x_entry.grid(row=0, column=1, padx=(0, 20), sticky=tk.W)

        ttk.Label(raw_container, text="Y:", width=2).grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        raw_y_var = tk.StringVar(value=f"{click_data.raw_y:.2f}")
        raw_y_entry = ttk.Entry(raw_container, textvariable=raw_y_var, width=15)
        raw_y_entry.grid(row=0, column=3, sticky=tk.W)

        # Adjusted coordinates section
        adj_label = ttk.Label(coord_frame, text="Adjusted Coordinates:", font=("Arial", 9, "bold"))
        adj_label.pack(anchor=tk.W, pady=(0, 5))

        adj_container = ttk.Frame(coord_frame)
        adj_container.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(adj_container, text="X:", width=2).grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        adj_x_var = tk.StringVar(value=f"{click_data.adjusted_x:.2f}")
        adj_x_entry = ttk.Entry(adj_container, textvariable=adj_x_var, width=15)
        adj_x_entry.grid(row=0, column=1, padx=(0, 20), sticky=tk.W)

        ttk.Label(adj_container, text="Y:", width=2).grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        adj_y_var = tk.StringVar(value=f"{click_data.adjusted_y:.2f}")
        adj_y_entry = ttk.Entry(adj_container, textvariable=adj_y_var, width=15)
        adj_y_entry.grid(row=0, column=3, sticky=tk.W)

        # Note section
        note_frame = ttk.Frame(coord_frame)
        note_frame.pack(fill=tk.X)

        note_text = (
            "Note: Editing raw coordinates will recalculate adjusted coordinates.\n"
            "Editing adjusted coordinates will update only the adjusted values."
        )
        note_label = ttk.Label(
            note_frame, text=note_text, font=("Arial", 8), foreground="gray", justify=tk.LEFT, wraplength=400
        )
        note_label.pack(anchor=tk.W)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(15, 10))

        def apply_changes():
            click_data.name = point_name_var.get()  # chang point name
            click_data.part = docpart_var.get()  # chang document part
            click_data.datatype = datatype_var.get()  # change data type
            click_data.alignment = align_var.get()  # change alignmant
            try:
                # Get new values
                new_raw_x = float(raw_x_var.get())
                new_raw_y = float(raw_y_var.get())
                new_adj_x = float(adj_x_var.get())
                new_adj_y = float(adj_y_var.get())

                # Check if raw coordinates changed
                if abs(new_raw_x - click_data.raw_x) > 0.01 or abs(new_raw_y - click_data.raw_y) > 0.01:
                    # Raw coordinates changed, recalculate adjusted
                    click_data.raw_x = new_raw_x
                    click_data.raw_y = new_raw_y

                    # Recalculate adjusted coordinates based on current origin
                    if self.pdf_document:
                        click_data.adjusted_x, click_data.adjusted_y = CoordinateTransformer.adjust_coordinates(
                            new_raw_x, new_raw_y, self.page_width, self.page_height, click_data.origin
                        )
                        click_data.mm_x = pt2mm(new_adj_x)
                        click_data.mm_y = pt2mm(new_adj_y)
                    else:
                        click_data.adjusted_x = new_adj_x
                        click_data.adjusted_y = new_adj_y
                        click_data.mm_x=pt2mm(new_adj_x)
                        click_data.mm_y=pt2mm(new_adj_y)
                else:
                    # Only adjusted coordinates changed
                    click_data.adjusted_x = new_adj_x
                    click_data.adjusted_y = new_adj_y
                    click_data.mm_x = pt2mm(new_adj_x)
                    click_data.mm_y = pt2mm(new_adj_y)

                # Update displays
                self.update_history_listbox()
                self.update_current_coords_display(click_data)

                # Redraw markers if on current page
                if self.pdf_document:
                    self.redraw_markers()

                # Select the edited point in the list
                self.history_listbox.selection_set(index)
                self.history_listbox.see(index)

                dialog.destroy()
                messagebox.showinfo("Success", f"Point #{index + 1} coordinates updated successfully!")

            except ValueError as e:
                messagebox.showerror("Error", f"Invalid coordinate values: {str(e)}")

        def cancel_edit():
            dialog.destroy()

        def delete_point():
            result = messagebox.askyesno(
                "Confirm Delete",
                f"Are you sure you want to delete Point #{index + 1}?\n\n"
                f"Page: {click_data.page_number}\n"
                f"Coordinates: ({click_data.adjusted_x:.2f}, {click_data.adjusted_y:.2f})",
            )
            if result:
                # Remove from history
                self.click_history.pop(index)

                # Update displays
                self.update_history_listbox()
                if self.click_history:
                    # Show the last remaining point, or clear display
                    if index > 0:
                        self.update_current_coords_display(self.click_history[index - 1])
                    elif self.click_history:
                        self.update_current_coords_display(self.click_history[0])
                else:
                    self.current_coords_label.config(text="Click on PDF to see coordinates")

                # Redraw markers
                if self.pdf_document:
                    self.redraw_markers()

                dialog.destroy()
                messagebox.showinfo("Success", f"Point #{index + 1} deleted successfully!")

        # Pack buttons with proper spacing and ensure visibility
        ttk.Button(button_frame, text="Delete", command=delete_point).pack(side=tk.LEFT, pady=10)
        ttk.Button(button_frame, text="Cancel", command=cancel_edit).pack(side=tk.RIGHT, pady=10)
        ttk.Button(button_frame, text="Apply", command=apply_changes).pack(side=tk.RIGHT, padx=(5, 0), pady=10)

        # Focus on first entry
        raw_x_entry.focus()
        raw_x_entry.select_range(0, tk.END)

    def on_marker_press(self, event):
        """Handle mouse press on canvas - check if clicking on a marker."""
        # Always set focus for mouse wheel scrolling
        self.canvas.focus_set()

        if not self.pdf_document:
            return

        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)

        # Find if we clicked on a marker (only if we have click history)
        point_index = -1
        if self.click_history:
            point_index = self.find_marker_at_position(canvas_x, canvas_y)

        if point_index != -1:
            # We clicked on an existing marker - start dragging
            self.dragging_point = point_index
            self.drag_data["x"] = canvas_x
            self.drag_data["y"] = canvas_y
            self.drag_data["point_index"] = point_index
            self.canvas.config(cursor="fleur")  # Change cursor to indicate dragging
        else:
            # Normal click behavior - add new point
            self.on_canvas_click(event)

    def on_marker_drag(self, event):
        """Handle dragging of a marker."""
        if self.dragging_point is None:
            return

        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)

        # Update marker position
        self.update_marker_position(self.dragging_point, canvas_x, canvas_y)

        # Update the coordinate data
        click_data = self.click_history[self.dragging_point]

        # Convert to PDF coordinates
        pdf_x = canvas_x / self.zoom_factor
        pdf_y = canvas_y / self.zoom_factor

        # Update raw coordinates
        click_data.raw_x = pdf_x
        click_data.raw_y = pdf_y

        # Recalculate adjusted coordinates
        origin = OriginPoint(self.selected_origin.get())
        click_data.adjusted_x, click_data.adjusted_y = CoordinateTransformer.adjust_coordinates(
            pdf_x, pdf_y, self.page_width, self.page_height, origin
        )
        click_data.origin = origin

        # Update displays
        self.update_current_coords_display(click_data)
        self.update_history_listbox()

        # Select the dragged point in history
        self.history_listbox.selection_clear(0, tk.END)
        self.history_listbox.selection_set(self.dragging_point)
        self.history_listbox.see(self.dragging_point)

    def on_marker_release(self, event):
        """Handle mouse release after dragging."""
        if self.dragging_point is not None:
            self.dragging_point = None
            self.canvas.config(cursor="")  # Reset cursor

    def find_marker_at_position(self, canvas_x, canvas_y):
        """Find if there's a marker at the given canvas position."""
        tolerance = 15  # Pixels tolerance for clicking on marker

        for i, click_data in enumerate(self.click_history):
            if click_data.page_number == self.current_page_number + 1:
                marker_x = click_data.raw_x * self.zoom_factor
                marker_y = click_data.raw_y * self.zoom_factor

                # Check if click is within tolerance of marker
                if abs(canvas_x - marker_x) <= tolerance and abs(canvas_y - marker_y) <= tolerance:
                    return i

        return -1

    def update_marker_position(self, point_index, new_canvas_x, new_canvas_y):
        """Update the visual position of a marker."""
        if point_index < 0 or point_index >= len(self.click_history):
            return

        click_data = self.click_history[point_index]
        if click_data.page_number != self.current_page_number + 1:
            return

        # Find and update the marker elements for this point
        # We need to redraw all markers
        # since we don't track individual marker IDs
        self.redraw_markers()

    def delete_selected_point(self):
        """Delete the selected point from history."""
        selection = self.history_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a point from the history list to delete.")
            return

        selected_index = selection[0]
        if selected_index >= len(self.click_history):
            messagebox.showerror("Error", "Invalid selection.")
            return

        click_data = self.click_history[selected_index]

        # Confirm deletion
        result = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete Point #{selected_index + 1}?\n\n"
            f"Page: {click_data.page_number}\n"
            f"Coordinates: ({click_data.adjusted_x:.2f}, {click_data.adjusted_y:.2f})",
        )

        if result:
            # Remove from history
            self.click_history.pop(selected_index)

            # Update displays
            self.update_history_listbox()
            if self.click_history:
                # Show the last remaining point, or clear display
                if selected_index > 0:
                    self.update_current_coords_display(self.click_history[selected_index - 1])
                    self.history_listbox.selection_set(selected_index - 1)
                elif self.click_history:
                    self.update_current_coords_display(self.click_history[0])
                    self.history_listbox.selection_set(0)
            else:
                self.current_coords_label.config(text="Click on PDF to see coordinates")

            # Redraw markers
            if self.pdf_document:
                self.redraw_markers()

            messagebox.showinfo("Success", f"Point #{selected_index + 1} deleted successfully!")


def get_screen_geometry(root):
    """Get available screen geometry accounting for taskbar and decorations."""
    # Update to ensure we have accurate measurements
    root.update_idletasks()

    # Get full screen dimensions
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    # Try to get actual available area (works on some systems)
    try:
        # This works on Windows to get the work area (screen minus taskbar)
        import ctypes

        # Get work area on Windows
        class RECT(ctypes.Structure):
            _fields_ = [
                ("left", ctypes.c_long),
                ("top", ctypes.c_long),
                ("right", ctypes.c_long),
                ("bottom", ctypes.c_long),
            ]

        rect = RECT()
        ctypes.windll.user32.SystemParametersInfoW(48, 0, ctypes.byref(rect), 0)

        work_width = rect.right - rect.left
        work_height = rect.bottom - rect.top - 40
        work_x = rect.left
        work_y = rect.top

        return work_width, work_height, work_x, work_y

    except Exception:
        # Fallback for non-Windows or if ctypes fails
        # Reserve space for taskbar (typically 40-80 pixels)
        work_width = screen_width
        work_height = screen_height - 80
        work_x = 0
        work_y = 0

        return work_width, work_height, work_x, work_y


def main():
    """Main application entry point."""
    # Create and configure the main window
    root = tk.Tk()

    # Set window icon and style (optional)
    root.configure(bg="#f0f0f0")

    # Create the PDF viewer application
    PDFViewer(root)

    # Get available screen area accounting for taskbar
    work_width, work_height, work_x, work_y = get_screen_geometry(root)

    # Set window size to 90% of available area for better fit
    window_width = min(1400, int(work_width * 0.9))
    window_height = min(900, int(work_height * 0.9))

    # Center the window in the work area
    x = work_x + (work_width - window_width) // 2
    y = work_y + (work_height - window_height) // 2

    # Ensure window doesn't go off-screen
    x = max(work_x, min(x, work_x + work_width - window_width))
    y = max(work_y, min(y, work_y + work_height - window_height))

    # Apply the calculated geometry
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")

    # Set minimum window size
    root.minsize(800, 600)

    # Start the GUI event loop
    root.mainloop()


if __name__ == "__main__":
    main()
