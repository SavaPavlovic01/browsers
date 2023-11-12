import tkinter as tk
import folder_browser
import os

window=tk.Tk()
label=tk.Label(text="Text")
entry = tk.Entry(width=50)
    

def on_click():
    print("Clicked")
    query=entry.get()
    res=folder_browser.search(query,"C:\\Users\\ps200536d\\Desktop\\browser\\folder_browser\\test")
    os.startfile(folder_browser.get_full_path(res[0][0]))

if __name__=="__main__":
    label.pack()
    entry.pack()
    button=tk.Button(command=on_click,text="Search")
    button.pack()
    window.mainloop()

