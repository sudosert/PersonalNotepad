import ConstructForm

main_form = ConstructForm.root

main_form.protocol("WM_DELETE_WINDOW", ConstructForm.confirm_save)
main_form.mainloop()

