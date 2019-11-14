#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import mimetypes
import threading
import os
import csv
from tkinter import *
from tkinter import filedialog, messagebox
from datetime import datetime

import pyexiv2
from PIL import Image, ImageTk


class TagLabel(Label):
    """Les étiquettes précisant les tags à saisir"""

    def __init__(self, boss, width=10, text=""):
        Label.__init__(self, boss, width=width, relief=RAISED, anchor=W,
                       borderwidth=0, padx=4, pady=4, text=text)


class TagEntry(Entry):
    """Les boîtes dans lesquelles l'utilisateur saisit les tags"""

    def __init__(self, boss, width=40, textvariable=""):
        self.v = StringVar()
        self.v.set(textvariable)
        Entry.__init__(self, boss, width=width, textvariable=self.v)


class MenuBar(Frame):
    """Barre de menus"""

    def __init__(self):
        Frame.__init__(self, borderwidth=2)

        # Menu Fichier
        file_menu = Menubutton(self, text="Fichier")
        file_menu.pack(side=LEFT)
        # Menu Chantier
        chantier_menu = Menubutton(self, text="Chantier")
        chantier_menu.pack(side=LEFT)
        # Menu Aide
        help_menu = Menubutton(self, text="Aide")
        help_menu.pack(side=RIGHT)
        # Partie déroulante, on y ajoute les entrées
        me1 = Menu(file_menu)
        me1.add_command(label="Ouvrir une image", underline=0, command=choose_img)
        me1.add_command(label="Ouvrir un dossier", underline=0, command=lambda: choose_dir(1))
        me1.add_command(label="Quitter", underline=0, command=quitter)
        me2 = Menu(chantier_menu)
        me2.add_command(label="Éditer les tags communs", underline=0, command=launch_global_tagger)
        me2.add_command(label="Export csv", underline=0, command=csv_export)
        me3 = Menu(help_menu)
        me3.add_command(label="Manuel", underline=0, command=show_help)
        me3.add_command(label="À propos", underline=0, command=show_about)
        # Intégration des éléments du menu
        file_menu.configure(menu=me1)
        chantier_menu.configure(menu=me2)
        help_menu.configure(menu=me3)


class GlobalTagger(Toplevel):
    """Une sous-fenêtre permettant d'appliquer des tags sur une arborescence complète"""

    def __init__(self):
        """Contructeur de la classe, sous-fenêtre Tk"""
        Toplevel.__init__(self)
        self.title("Éditeur de tags Exif")

        tag_labels = ["Dossier", "Auteur", "Chantier"]
        # Création des étiquettes
        for i, e in enumerate(tag_labels):
            tlabel = TagLabel(self, text=e)
            tlabel.grid(row=(0 + i), column=0)

        # Ce champ affiche le nom du dossier choisi
        self.gchantier_name = TagLabel(self, text="")
        self.gchantier_name.grid(row=0, column=1, columnspan=2)
        # Les champs des tags globaux
        self.gauteur_entry = TagEntry(self)
        self.gauteur_entry.grid(row=1, column=1, columnspan=2)
        self.gchantier_entry = TagEntry(self)
        self.gchantier_entry.grid(row=2, column=1, columnspan=2)

        self.b_open = Button(self, text="Ouvrir...", command=self.open_dir)
        self.b_open.grid(row=4, column=0)
        self.b_write = Button(self, text="Écrire", command=self.tag_recursively)
        self.b_write.grid(row=4, column=1)
        self.b_quit = Button(self, text="Fermer", command=self.destroy)
        self.b_quit.grid(row=4, column=2)

    def open_dir(self):
        """Sélectionner un dossier racine, afficher son nom"""
        choose_dir(0)
        self.gchantier_name.configure(text=os.path.basename(img_dir))

    def tag_recursively(self):
        """Parcourir le dossier récursivement et appliquer les tags sur chaque fichier"""
        global img_dir
        # On parcourt le dossier à la recherche de fichiers
        for dirpath, dirs, files in os.walk(img_dir):
            for filename in files:
                # Vérification que c'est bien une image
                if not_mimetype(filename) == 1:
                    # Si pas une image on passe au fichier suivant
                    continue
                else:
                    # On applique les tags saisis
                    metadata = pyexiv2.ImageMetadata(dirpath + "/" + filename)
                    metadata.read()
                    metadata["Exif.Image.Artist"] = self.gauteur_entry.v.get()
                    metadata["Exif.Photo.UserComment"] = self.gchantier_entry.v.get()
                    metadata.write()
        # Une fois l'opération terminée, on avertit l'utilisateur
        messagebox.showinfo("Opération terminée", "Les photos ont été correctement étiquetées.")


class Aide(Toplevel):
    """Sous fenêtre d'aide"""

    def __init__(self):
        # Constructeur de la classe sous-fenêtre Tk
        Toplevel.__init__(self)
        self.title("Aide")

        self.aide = Label(self, takefocus=0, text=self.get_help(), justify=LEFT)
        self.aide.pack()

    def get_help(self):
        """Lire le fichier README et l'afficher"""
        with open("HELP.txt", "r") as f:
            help_text = f.read()

        return help_text


def show_help():
    """Affiche l'aide dans une sous-fenêtre"""
    Aide()


def show_about():
    """Affiche la licence et le contact de l'auteur de ce logiciel"""
    messagebox.showinfo("À propos de ce logiciel", "Ce logiciel a été écrit pour le personnel d'Éveha.\n\
Il est diffusé sous la licence libre GNU GPLv3 ou supérieure.\n\n\
Auteur  : sogal\n\
Contact : sogal@opensuse.org\n\
Version : 0.2")


def launch_global_tagger():
    """Afficher l'utilitaire de tags récursif"""
    GlobalTagger()


def choose_dir(show):
    """Choisir et mémoriser le dossier racine contenant les images à traiter"""
    img_extensions = ('.png', '.PNG', '.jpg', '.JPG')
    global img_dir
    if img_dir != "":
        open_dir = img_dir
    else:
        open_dir = os.path.expanduser("~/")
    global img_path
    global img_list
    img_list = []
    img_dir = filedialog.askdirectory(initialdir=(open_dir), title="Choisir le dossier contenant les \
images du chantier", mustexist=True)
    # On vérifie qu'un dossier a bien été sélectionné
    if img_dir:
        # Si oui, on le parcourt et on liste les fichiers trouvés
        for dirpath, dirs, files in os.walk(img_dir):
            for filename in files:
                img_list.append(os.path.join(dirpath, filename))
        # On filtre la liste pour ne garder que les images
        img_list = ["{}".format(i) for i in img_list if os.path.splitext(i)[1] in img_extensions]
        img_path = img_list[0]
        # On affiche la première image de la liste si nécessaire
        if show == 1:
            show_img(img_path)

        return img_list
    else:
        # Si non, on avertit l'utilisateur
        messagebox.showerror("Dossier manquant", "Aucun dossier choisi, ce programme ne peut continuer.")
        return 1


def choose_img():
    """Ouvre un dialogue permettant de choisir une image dont le chemin est renvoyé"""
    img_extensions = ('.png', '.PNG', '.jpg', '.JPG')
    global img_dir
    global img_list
    img_list = []
    global img_path
    img_path = filedialog.askopenfilename(initialdir=(os.path.expanduser(
        img_dir)), filetypes=[('Images', img_extensions), ('Tout', '.*')],
        title="Image à ouvrir", parent=w)
    # On vérifie qu'une image a été choisie
    if img_path:
        # Si oui on l'affiche
        show_img(img_path)
        img_dir = os.path.dirname(img_path)
        # Puis on parcourt son dossier à la recherche d'autres images que l'on liste
        for dirpath, dirs, files in os.walk(img_dir):
            for filename in files:
                img_list.append(os.path.join(dirpath, filename))
        # On filtre la liste pour ne conserver que les images
        img_list = ["{}".format(i) for i in img_list if os.path.splitext(i)[1] in img_extensions]
        return img_list
    else:
        # Si non, on avertit l'utilisateur
        messagebox.showerror("Fichier manquant", "Aucun fichier image choisi, ce programme ne peut continuer.")
        return 1


def not_mimetype(file):
    """Vérification du type MIME du fichier pour éviter les erreurs lors
    de la lecture ou écriture des tags"""
    mimet = mimetypes.guess_type(file)[0]
    if not mimet or "image" not in mimet:
        return 1
    else:
        return 0


def resize_img(image):
    """Redimensionne l'image au côté max de son conteneur"""
    x, y = image.size[0], image.size[1]
    if x > 800 or y > 600:
        if x > y:
            y = int((800 * y) / x)
            x = 800
        else:
            x = int((x * 600) / y)
            y = 600
        image = image.resize((x, y), Image.ANTIALIAS)
    # Après redimensionnement, l'image (son conteneur) doit toujours rester centrée verticalement
    imgcan.pack_configure(ipady=600 - y)
    return image


def get_tags(path):
    """Lire les metadonnées et les afficher à leur place"""
    metadata = pyexiv2.ImageMetadata(path)
    metadata.read()
    a = "Exif.Image.Artist"
    b = "Exif.Photo.DateTimeOriginal"
    c = "Exif.Photo.UserComment"
    d = "Exif.Image.ImageDescription"
    # On vérifie que ces tags existent
    for tag in a, b, c, d:
        if tag not in metadata.exif_keys:
            metadata[tag] = ""
    # On les affiche dans les boîtes Entry correspondantes après formatage
    # Si la date est vide, impossible de la formater, la valeur du champ reste vide
    try:
        date_entry.v.set(metadata[b].value.strftime('%A %d %B %Y'))
    except:
        date_entry.v.set("")
    auteur_entry.v.set(metadata[a].value)
    descrip_entry.v.set(metadata[d].value)
    # Si le commentaire est composé de valeurs au format .csv (liées par des ;)
    if ";" in list(metadata[c].value):
        c = metadata[c].value
        # On les sépare dans une liste
        comment_list = c.split(";")
        view = comment_list[0]
        comment = comment_list[1]
        view_entry.v.set(view)
        chantier_entry.v.set(comment)
    else:
        # Sinon on affiche le tag UserComment au complet
        comment = metadata[c].value
        chantier_entry.v.set(comment)


def get_img_name(path):
    """Récupérer et afficher le nom du fichier image"""
    name = os.path.basename(path)
    img_name.configure(text=name)


def delete_img(path):
    """Supprimer l'image actuellement affichée après confirmation de l'uttlisateur"""
    # On vérifie qu'une image est active ( = affichée)
    if img_path:
        name = os.path.basename(path)
        if messagebox.askokcancel("Supprimer l'image", "Voulez-vous vraiment supprimer " + name + " ?",
                                  icon="warning"):
            if len(img_list) > 1:
                # On affiche l'image suivante
                navigate("next")
            else:
                # Sauf si la liste n'en contenait qu'une
                imgcan.configure(image="")
                img_name.configure(text="")
            # On sort l'image à supprimer de la liste
            img_list.pop(img_list.index(path))
            # Puis on l'efface
            os.remove(path)


def quitter():
    """Demander confirmation avant de quitter"""
    if messagebox.askokcancel("Quitter", "Voulez-vous vraiment quitter l'application ?"):
        w.quit()


def show_img(path):
    """Affiche l'image redimensionnée et ses infos, noms et tags Exif"""
    # Choisir l'image
    img1 = Image.open(path)
    # La redimensionner si nécessaire
    imgr = resize_img(img1)
    # Créer un objet Image
    img2 = ImageTk.PhotoImage(imgr)
    # Qu'on garde en mémoire pour éviter sa destruction par le ramasse-miettes de Python
    dicimg['img3'] = img2
    # On insère notre image à sa place
    imgcan.configure(image=img2)
    imgcan.image = img2
    imgcan.path = img2
    # On affiche le nom de l'image
    get_img_name(path)
    # On affiche les tags de l'image
    get_tags(path)


def clean_tag_entries():
    """Nettoyer les champs entre chaque photo"""
    for entry in (date_entry, auteur_entry, view_entry, descrip_entry, chantier_entry):
        entry.v.set("")


def navigate(sens):
    """Permet de naviguer dans la liste des images contenues dans le dossier choisi"""
    global img_path
    global img_list
    img_pos = 0
    # On vérifie qu'il reste des images dans la liste (utile après suppression de la dernière image d'un dossier)
    if len(img_list) > 0:
        # On vérifie qu'il y a plus d'une seule image dans la liste
        if len(img_list) > 1:
            # On récupère la position de l'image active dans la liste
            img_index = img_list.index(img_path)
            if sens == "prev":
                img_pos = img_index - 1
                if img_pos < 0:
                    img_pos = len(img_list) - 1
            elif sens == "next":
                img_pos = img_index + 1
                if img_pos > len(img_list) - 1:
                    img_pos = 0
            # L'image active est celle occupant la nouvelle position
            img_path = (img_list[img_pos])
        clean_tag_entries()
        # S'il s'avère que l'image active n'est pas vraiment une image ( mimetype != image), on passe à la suivante
        if not_mimetype(img_path) == 1:
            navigate("next")
        else:
            # Si c'est bon, on l'affiche
            show_img(img_path)


def set_tags(path):
    """Modifier ou créer les metadonnées Exif de l'image affichée"""
    if img_path:
        metadata = pyexiv2.ImageMetadata(path)
        metadata.read()
        metadata["Exif.Image.Artist"] = auteur_entry.v.get()
        metadata["Exif.Image.ImageDescription"] = descrip_entry.v.get()
        # On agrège les valeurs de certains champs au format .csv
        metadata["Exif.Photo.UserComment"] = view_entry.v.get() + ";" + chantier_entry.v.get()
        metadata.write()
        messagebox.showinfo("Opération terminée", "Cette photo a été correctement étiquetée.")


def csv_export():
    """Choisir le dossier contenant les photos, lire les tags, les exporter dans un fichier .csv"""
    photos_list = choose_dir(0)

    if img_dir:

        messagebox.showinfo("Export CSV", "Export en cours, veuillez patienter, un message vous informera \n\
de la bonne fin des opérations")

        def write_tags():
            """Fonction principale d'export des tags dans un fichier"""

            # Ouverture du fichier listing.csv dans le dossier 'img_dir'
            with open(img_dir+"/listing.csv", 'w', newline='') as f:
                listing_csv = csv.writer(f, delimiter=',')
                # On passe chaque photo en revue
                for photo in photos_list:
                    photo_tags_list = []
                    metadata = pyexiv2.ImageMetadata(photo)
                    metadata.read()
                    # On vérifie que les tags demandés existent bien dans les photos
                    for tag in ["Exif.Image.Artist",
                                "Exif.Image.ImageDescription",
                                "Exif.Photo.DateTimeOriginal",
                                "Exif.Photo.UserComment"]:
                        # Si oui on insère leur valeur dans une liste...
                        if tag in metadata.exif_keys:
                             if tag == "Exif.Photo.DateTimeOriginal":
                                 old_date = metadata[tag].value
                                 new_date = datetime.strptime(
                                     str(old_date), '%Y-%m-%d %H:%M:%S').strftime(
                                        '%d/%m/%Y %H:%M:%S')
                                 photo_tags_list.append(new_date)
                             else:
                                 photo_tags_list.append(metadata[tag].value)
                    listing_csv.writerow([os.path.dirname(photo)] +
                                         [os.path.basename(photo)] +
                                         photo_tags_list)
            messagebox.showinfo("Export CSV", "Export des métadonnées vers listing.csv terminé.")

        # Création d'un thread parallèle pour que l'application ne paraisse pas "freezée" lors de longs exports
        thread = threading.Thread(target=write_tags)
        thread.daemon = True
        thread.start()


if __name__ == "__main__":
    # Initialisation des variables globales
    img_path = ""
    img_dir = ""
    img_list = []
    dicimg = {}

    # La fenêtre principale
    w = Tk()
    w.resizable(width=False, height=False)
    w.title("Apee : éditeur de métadonnées Exif pour photos archéologiques")

    # Tk Call pour forcer l'ajout d'un filtre pour "dot{file,dir}"
    try:
        # Tentative d'initialisation d'un dialogue factice pour pouvoir passer les
        # variables qui vont bien
        try:
            w.tk.call('tk_getOpenFile', '-foobar')
        except TclError:
            pass
        w.tk.call('set', '::tk::dialog::file::showHiddenBtn', '1')
        w.tk.call('set', '::tk::dialog::file::showHiddenVar', '0')
    except:
        pass

    # Icône du logiciel
    ico = PhotoImage(file="apee.png")
    #ico = PhotoImage(file="/usr/local/share/apee/apee.png")
    w.call('wm', 'iconphoto', w, ico)

    # La barre de menu
    menu = MenuBar()
    menu.grid(row=0, column=0, sticky=W)

    # Le cadre de gauche qui servira à afficher l'image
    imgframe = Frame(w, bd=2, bg="#444444", width=800, height=600, padx=5, pady=5)
    # On force la mise à la taille définie ci-dessus
    imgframe.pack_propagate(0)
    imgframe.grid(row=1, column=0, sticky=NW, padx=5, pady=5)
    # Le conteneur qui contiendra l'image affichée
    imgcan = Label(imgframe, background="#444444", text="Choisissez une image pour l'afficher ici", image="")
    imgcan.pack()
    imgcan.pack_configure(ipady=600)

    # Le cadre de droite qui contient les éléments de contrôle
    ctlframe = Frame(w, bd=1, padx=5, pady=5)
    ctlframe.grid(row=1, column=1, sticky=NE)

    # Création en chaîne des étiquettes de champs
    tag_labels = ["Date", "Auteur", "Description", "Vue depuis", "Chantier"]
    for i, e in enumerate(tag_labels):
        tlabel = TagLabel(ctlframe, text=e)
        tlabel.grid(row=(1 + i), column=0)

    # Étiquette affichant le nom de l'image active
    img_name = Label(ctlframe, text="", padx=5, pady=5)
    img_name.grid(row=0, column=1, columnspan=3)

    # Création des champs pour les metadonnées Exif
    date_entry = TagEntry(ctlframe)
    date_entry.grid(row=1, column=1, columnspan=2)
    auteur_entry = TagEntry(ctlframe)
    auteur_entry.grid(row=2, column=1, columnspan=2)
    descrip_entry = TagEntry(ctlframe)
    descrip_entry.grid(row=3, column=1, columnspan=2)
    view_entry = TagEntry(ctlframe)
    view_entry.grid(row=4, column=1, columnspan=2)
    chantier_entry = TagEntry(ctlframe)
    chantier_entry.grid(row=5, column=1, columnspan=2)

    # Boutons de navigation et étiquette du nom de l'image
    Button(ctlframe, text="<", padx=5, pady=5, takefocus=0, command=lambda: navigate("prev")).grid(row=6,
                                                                                                   column=0, sticky=W)
    Button(ctlframe, text=">", padx=5, pady=5, takefocus=0, command=lambda: navigate("next")).grid(row=6,
                                                                                                   column=2, sticky=E)

    # Boutons de choix d'image, d'écriture des tags définis et de sortie
    Button(ctlframe, text="Enregistrer", pady=5, takefocus=1, command=lambda: set_tags(img_path)).grid(row=6, column=1)
    # Forcer la taille de la dernière ligne
    ctlframe.rowconfigure(7, minsize=410)
    Button(ctlframe, text="Ouvrir...", pady=5, takefocus=0, command=lambda: choose_img()).grid(row=7,
                                                                                               column=0,
                                                                                               sticky=SW)
    Button(ctlframe, text="Supprimer", pady=5, takefocus=0, command=lambda: delete_img(img_path)).grid(row=7,
                                                                                                       column=1,
                                                                                                       sticky=S)
    Button(ctlframe, text="Quitter", pady=5, takefocus=0, command=lambda: quitter()).grid(row=7, column=2,
                                                                                          sticky=SE)

    # Contrôle clavier
    w.bind("<Left>", lambda e: navigate("prev"))
    w.bind("<Right>", lambda e: navigate("next"))
    w.bind("<Control - q>", lambda e: quitter())
    w.bind("<Control - s>", lambda e: set_tags(img_path))
    w.bind("<Control - o>", lambda e: choose_img(1))
    w.bind("<Control - O>", lambda e: choose_dir(0))

    w.mainloop()
