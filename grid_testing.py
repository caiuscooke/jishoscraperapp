from customtkinter import *


def print_bbox(event, frame: CTkFrame):
    for row in range(10):
        for column in range(10):
            x, y, width, height = frame.bbox(row=row, column=column)
            print(f'Coords {row}/{column}')
            print(f'Width: {width}')
            print(f'Height: {height}')


root = CTk()
frame = CTkFrame(root)
frame.pack(fill='both', expand=True)
frame.grid_columnconfigure([i for i in range(10)], uniform='a', weight=1)
frame.grid_rowconfigure([i for i in range(10)], uniform='a', weight=1)
for row in range(10):
    for column in range(10):
        if row % 2 == 0:
            if column % 2 == 0:
                CTkLabel(frame, text=column, bg_color='black').grid(
                    row=row, column=column, sticky='nsew')
            else:
                CTkLabel(frame, text=column, bg_color='white').grid(
                    row=row, column=column, sticky='nsew')
        else:
            if column % 2 == 0:
                CTkLabel(frame, text=column, bg_color='white').grid(
                    row=row, column=column, sticky='nsew')
            else:
                CTkLabel(frame, text=column, bg_color='black').grid(
                    row=row, column=column, sticky='nsew')
        print(frame.bbox(column=column, row=row))

frame.bind("<Configure>", lambda event, frame=frame: print_bbox(event, frame))

root.mainloop()
