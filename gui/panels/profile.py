import customtkinter as ctk
import tkinter.messagebox as tkmb
import tkinter.simpledialog as tk_sd
import tkinter.filedialog as filedialog
from gui.styles.colors import COLORS
from gui.i18n import _
from ftesc.profiles import (
    save_profile, load_profile, list_profiles, delete_profile,
    export_profile, import_profile,
)
from ftesc import DualMotorConfig


class ProfilePanel(ctk.CTkFrame):
    def __init__(self, parent, on_collect_config=None, on_apply_config=None, **kwargs):
        super().__init__(parent, **kwargs)
        self._on_collect = on_collect_config
        self._on_apply = on_apply_config

        ctk.CTkLabel(self, text=_("profile.section_title"),
            font=ctk.CTkFont(size=14, weight='bold'),
            text_color=COLORS['accent_green']).pack(pady=(10, 5), padx=15, anchor='w')
        ctk.CTkFrame(self, height=2, fg_color=COLORS['bg_light']).pack(fill='x', padx=15, pady=(0, 8))

        ctk.CTkButton(self, text=_("profile.save_button"),
            command=self._on_save_profile,
            fg_color=COLORS['accent_green'], hover_color=COLORS['success'],
            font=ctk.CTkFont(size=11), height=28).pack(padx=15, pady=(0, 4), fill='x')

        ctk.CTkButton(self, text=_("profile.load_button"),
            command=self._on_load_profile,
            fg_color=COLORS['accent_blue'], hover_color=COLORS['accent'],
            font=ctk.CTkFont(size=11), height=28).pack(padx=15, pady=(0, 4), fill='x')

        self._profile_list_var = ctk.StringVar(value=_("profile.load_default"))
        self._profile_list_menu = ctk.CTkOptionMenu(self,
            variable=self._profile_list_var,
            values=[_("profile.load_default")],
            fg_color=COLORS['bg_dark'], button_color=COLORS['accent_blue'],
            font=ctk.CTkFont(size=11), width=120)
        self._profile_list_menu.pack(padx=15, pady=(0, 4))

        ctk.CTkButton(self, text=_("profile.export_button"),
            command=self._on_export_profile,
            fg_color=COLORS['bg_light'], hover_color=COLORS['accent_blue'],
            font=ctk.CTkFont(size=11), height=28).pack(padx=15, pady=(0, 4), fill='x')

        ctk.CTkButton(self, text=_("profile.import_button"),
            command=self._on_import_profile,
            fg_color=COLORS['bg_light'], hover_color=COLORS['accent_green'],
            font=ctk.CTkFont(size=11), height=28).pack(padx=15, pady=(0, 4), fill='x')

        ctk.CTkButton(self, text=_("profile.delete_button"),
            command=self._on_delete_profile,
            fg_color=COLORS['danger'], hover_color='#b91c1c',
            font=ctk.CTkFont(size=11), height=28).pack(padx=15, pady=(0, 4), fill='x')

        self._refresh_profile_list()

    def _refresh_profile_list(self):
        profiles = list_profiles()
        values = [_("profile.load_default")] + (profiles or [])
        self._profile_list_menu.configure(values=values)
        self._profile_list_var.set(_("profile.load_default"))

    def _on_save_profile(self):
        name = tk_sd.askstring(
            _("profile.save.dialog_title"),
            _("profile.save.dialog_text"))
        if not name:
            return
        try:
            config = self._on_collect()
            errors = config.validate()
            has_errors = any(errors[k] for k in errors)
            if has_errors:
                all_errs = []
                for section, errs in errors.items():
                    if errs:
                        all_errs.append(f"  {section}: {'; '.join(errs)}")
                msg = _("app.profile.save.validation_warnings") + "\n" + "\n".join(all_errs)
                if not tkmb.askyesno(_("app.profile.save.validation_warnings"),
                    msg + "\n\n" + _("app.profile.save.save_anyway")):
                    return
            config.name = name
            save_profile(name, config)
            self._refresh_profile_list()
            tkmb.showinfo(_("profile.save.dialog_title"),
                _("app.profile.save.success").format(name=name))
        except ValueError as e:
            tkmb.showerror(_("profile.error.title"),
                _("profile.error.save_failed").format(e=e))
        except Exception as e:
            tkmb.showerror(_("profile.error.title"),
                _("profile.error.save_failed").format(e=e))

    def _on_load_profile(self):
        name = self._profile_list_var.get()
        if name == _("profile.load_default"):
            tkmb.showinfo(_("profile.load.info_title"),
                _("profile.load.select_first"))
            return
        try:
            config = load_profile(name)
            if config is None:
                tkmb.showerror(_("profile.error.title"),
                    _("profile.error.not_found").format(name=name))
                return
            self._on_apply(config)
            tkmb.showinfo(_("profile.load.info_title"),
                _("app.profile.load.success").format(name=name))
        except Exception as e:
            tkmb.showerror(_("profile.error.title"),
                _("app.error.load_failed").format(e=e))

    def _on_export_profile(self):
        name = self._profile_list_var.get()
        if name == _("profile.load_default"):
            tkmb.showinfo(_("profile.export.info_title"),
                _("profile.export.select_first"))
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[(_("profile.filetype.json"), "*.json"),
                       (_("profile.filetype.all"), "*.*")],
            initialfile=f"{name}.json",
            title=_("profile.export.dialog_title"))
        if not path:
            return
        if export_profile(name, path):
            tkmb.showinfo(_("profile.export.info_title"),
                _("profile.export.success").format(path=path))
        else:
            tkmb.showerror(_("profile.error.title"),
                _("profile.error.export_failed"))

    def _on_import_profile(self):
        path = filedialog.askopenfilename(
            filetypes=[(_("profile.filetype.json"), "*.json"),
                       (_("profile.filetype.all"), "*.*")],
            title=_("profile.import.dialog_title"))
        if not path:
            return
        try:
            config = import_profile(path)
            if config is None:
                tkmb.showerror(_("profile.error.title"),
                    _("app.profile.import.invalid_file"))
                return
            self._on_apply(config)
            if config.name:
                self._profile_list_var.set(config.name)
            self._refresh_profile_list()
            tkmb.showinfo(_("profile.import.dialog_title"),
                _("profile.import.success").format(name=config.name or ""))
        except Exception as e:
            tkmb.showerror(_("profile.error.title"),
                _("profile.error.invalid_json").format(e=e))

    def _on_delete_profile(self):
        name = self._profile_list_var.get()
        if name == _("profile.load_default"):
            tkmb.showinfo(_("profile.delete.confirm_title"),
                _("profile.load.select_first"))
            return
        if not tkmb.askyesno(_("profile.delete.confirm_title"),
            _("profile.delete.confirm_text").format(name=name)):
            return
        try:
            delete_profile(name)
            self._refresh_profile_list()
            tkmb.showinfo(_("profile.delete.confirm_title"),
                _("app.profile.delete.success").format(name=name))
        except Exception as e:
            tkmb.showerror(_("profile.error.title"),
                _("app.error.delete_failed").format(e=e))
