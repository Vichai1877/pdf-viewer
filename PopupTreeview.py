#============================================================================================================
import tkinter as tk
from tkinter import ttk


def Treeview_Sort_Column(tv, col, reverse):
    data_list = [(tv.set(item, col), item) for item in tv.get_children('')]
    data_list.sort(reverse=reverse)
    for index, (val, item) in enumerate(data_list):
        tv.move(item, '', index)
    tv.heading(col, command=lambda: Treeview_Sort_Column(tv, col, not reverse))

class PopupTView(tk.Toplevel) :
    def __init__(self,master,
                 width : int = 300,             # width of treeview
                 columns : list = None,         # columns name
                 columns_width: list = None,    # columns width
                 columns_anchor : list =None,   # columns anchor
                 show : str = "headings",       # show parameter
                 height : int = 16,             # height of treeview
                 values : list = None,          # values data (list)
                 callbackfunc : str = None,     # call back when selected item by double click or enter
                 **kwargs):
        super().__init__(master,**kwargs)
        self.master = master
        self.callbackfunc = callbackfunc
        self.wm_overrideredirect(True)  # ไม่มีกรอบหน้าต่าง
        self.lift()
        self.geometry(self.get_geometry(width=width,height=height))
        frame = ttk.Frame(self)
        frame.pack(fill="both", expand=True)
        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side="right", fill="y")
        self.treeview = ttk.Treeview(frame, columns=columns, show=show,
                                     height=height, yscrollcommand=scrollbar.set,)
        self.treeview.pack(side="left", fill="both", expand=True)
        # creat heading - - - - - - - - - - - - - -
        if columns:
            for (col,wid,anc) in zip(columns,columns_width,columns_anchor):
                self.treeview.heading(col, text=col, command=lambda _col=col: Treeview_Sort_Column(self.treeview, _col, False))
                #self.treeview.heading(col, text=col)
                self.treeview.column(col,width=wid,anchor=anc)
        scrollbar.config(command=self.treeview.yview)
        self.ChangeValues(values=values) # setup treeview values
        self.treeview.bind("<Double-1>", self.On_TreeView_Select)
        self.treeview.bind("<Return>", self.On_TreeView_Select)
        self.bind("<Escape>", self.On_Escape)
        self.bind("<Leave>",self.On_Escape)
        self.bind("<Button-1>", self.On_MouseClick)
        self.bind("<KeyPress>",self.On_KeyPress)  # ดัก keypress ถ้าพิมพ์ อักษร ก็ส่ง ให้ไป focus entry แทน
        #self.grab_set()
        self.focus_set()

    def get_geometry(self,width,height):
        x = self.master.winfo_rootx()
        y = self.master.winfo_rooty() + self.master.winfo_height()
        w = width
        h = height*20 # height * font height
        geotext = f"{w}x{h}+{x}+{y}"
        return geotext

    def ChangeValues(self,values):  # set values to treeview
        self.treeview.delete(*self.treeview.get_children()) # clear treeview
        if values :  # not blank list
            for row in values :
                self.treeview.insert("",tk.END,values=row)
            items = self.treeview.get_children()
            if items:
                first_item = items[0]
                self.treeview.selection_set(first_item)
                self.treeview.focus(first_item)
                self.treeview.see(first_item)

    def On_TreeView_Select(self,event):  # treeview selected (by double click/ enter key)
        item = self.treeview.selection()
        row = self.treeview.item(item)["values"]
        #print(f"SELECT item={item}  row={row}")
        if self.callbackfunc :
            self.callbackfunc(row)  # send row to callbackfunc
        self.destroy()
        return "break"

    def On_KeyPress(self,event):
        if event.char or event.keysym in ["BackSpace", "Delete"]:
            self.master.Focus()
            return
        return

    def On_Escape(self,event):  # on escape destroy
        self.destroy()

    def On_MouseClick(self,event : tk.Event):  # check mouse click out side of treeview if true destroy
        x = event.x_root
        y = event.y_root
        #print(f"x={x} y={y}")
        if not (self.winfo_rootx() <= x <= self.winfo_rootx() + self.winfo_width() and
                self.winfo_rooty() <= y <= self.winfo_rooty() + self.winfo_height()):

            self.destroy()

    def Focus(self):  # focus treeview
        self.treeview.focus_set()

    def CountTreeviewValues(self):
        return len(self.treeview.get_children())

    def destroy(self):
        #self.grab_release()
        super().destroy()
