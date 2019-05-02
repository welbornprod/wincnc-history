#!/usr/bin/env python3

""" WinCNC - Libraries - GUI - Dialogs
    Handles dialog boxes for WinCNC.
    * This file must not import any other local modules.
    -Christopher Welborn 05-01-2019
"""
import tkinter as tk
from tkinter import messagebox


NAME = 'WinCNC-History'


def show_done_msg(msg, errors=0):
    """ Shows either a success or error dialog, based on whether `errors` is
        non-zero.
    """
    titletype = 'Success'
    if errors:
        titletype = '{} {}'.format(
            errors,
            'Error' if errors == 1 else 'Errors',
        )
    title = '{} - {}'.format(NAME, titletype)
    if errors:
        messagebox.showerror(title=title, message=msg)
    else:
        messagebox.showinfo(title=title, message=msg)


def show_error(msg, parent=None):
    """ Show a tkinter error dialog. """
    win = None
    if parent is None:
        win = tk.Tk()
        # Fix message boxes.
        win.option_add('*Dialog.msg.font', ('Arial', 10))
        win.withdraw()
    title = f'{NAME} - Error'
    messagebox.showerror(title=title, message=str(msg))
    if win is not None:
        win.destroy()


def show_info(msg, title=None, parent=None):
    """ Show a tkinter info dialog. """
    win = None
    if parent is None:
        win = tk.Tk()
        # Fix message boxes.
        win.option_add('*Dialog.msg.font', ('Arial', 10))
        win.withdraw()

    utitle = f' - {title}' if title else ''
    title = f'{NAME}{utitle}'
    messagebox.showinfo(title=title, message=str(msg))
    if win is not None:
        win.destroy()


def show_question(msg, title=None, parent=None):
    """ Show a tkinter askyesno dialog. """
    win = None
    if parent is None:
        win = tk.Tk()
        # Fix message boxes.
        win.option_add('*Dialog.msg.font', ('Arial', 10))
        win.withdraw()

    utitle = title or 'Confirm'
    title = f'{NAME} - {utitle}'
    ret = messagebox.askyesno(title=title, message=str(msg))
    if win is not None:
        win.destroy()
    return ret


def show_warning(msg, title=None):
    """ Show a tkinter warning dialog. """
    title = '{} - {}'.format(NAME, title or 'Warning')
    return messagebox.showwarning(title=title, message=str(msg))
