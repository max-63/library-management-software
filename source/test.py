import sqlite3 as sq
import tkinter as tk
from tkinter import ttk, messagebox
import datetime

# Connexion à la base de données
connect = sq.connect("bibliotheque.db")
cur = connect.cursor()

# Fonction pour vérifier et créer les tables si elles n'existent pas
def create_tables():
    cur.execute("""
    CREATE TABLE IF NOT EXISTS Livre (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        auteur TEXT,
        date_ajout TEXT,
        titre TEXT,
        serie TEXT,
        type TEXT,
        tome INTEGER
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS Pret (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_livre INTEGER,
        nom TEXT,
        prenom TEXT,
        date_pret TEXT,
        FOREIGN KEY(id_livre) REFERENCES Livre(id)
    )
    """)
    connect.commit()

# Appel de la fonction pour créer les tables
create_tables()

# Fonction pour récupérer les données de la base de données
def fetch_data(titre="", auteur="", serie="", tome=""):
    query = """
    SELECT L.*, CASE WHEN P.id IS NOT NULL THEN 1 ELSE 0 END AS prete
    FROM Livre L
    LEFT JOIN Pret P ON L.id = P.id_livre
    WHERE 1=1
    """
    params = []
    if titre:
        query += " AND L.titre LIKE ?"
        params.append('%' + titre + '%')
    if auteur:
        query += " AND L.auteur LIKE ?"
        params.append('%' + auteur + '%')
    if serie:
        query += " AND L.serie = ?"
        params.append(serie)
    if tome:
        query += " AND L.tome = ?"
        params.append(tome)
    
    cur.execute(query, params)
    rows = cur.fetchall()
    return rows

# Fonction pour récupérer les valeurs uniques d'une colonne
def fetch_unique_values(column):
    cur.execute(f"SELECT DISTINCT {column} FROM Livre")
    return [row[0] for row in cur.fetchall()]

# Fonction pour vérifier les doublons
def check_duplicate(auteur, titre, serie):
    cur.execute("SELECT * FROM Livre WHERE auteur = ? AND titre = ? AND serie = ?", (auteur.upper(), titre.upper(), serie.upper()))
    return cur.fetchone() is not None

# Fonction pour supprimer un livre par son ID
def delete_livre(id_livre, tree, titre_combobox, auteur_combobox, serie_combobox, serie_combobox_add):
    try:
        cur.execute("DELETE FROM Livre WHERE id=?", (id_livre,))
        connect.commit()
        messagebox.showinfo("Suppression réussie", f"Le livre avec l'ID {id_livre} a été supprimé de la base de données.")
        refresh_table(tree)  # Rafraîchit le tableau après la suppression
        refresh_comboboxes(titre_combobox, auteur_combobox, serie_combobox, serie_combobox_add)
    except sq.Error as e:
        messagebox.showerror("Erreur de suppression", f"Erreur lors de la suppression du livre : {e}")

# Fonction pour ajouter un livre à la base de données
def ajout_livre(auteur, titre, serie, type_livre, tome, tree, titre_combobox, auteur_combobox, serie_combobox, serie_combobox_add):
    if check_duplicate(auteur, titre, serie):
        messagebox.showwarning("Doublon détecté", f"Le livre '{titre}' écrit par {auteur} dans la série '{serie}' existe déjà dans la base de données.")
        return

    try:
        date_ajout = str(datetime.date.today())
        var = (auteur.upper(), date_ajout, titre.upper(), serie.upper(), type_livre.upper(), int(tome))
        cur.execute("INSERT INTO Livre (auteur, date_ajout, titre, serie, type, tome) VALUES (?, ?, ?, ?, ?, ?)", var)
        connect.commit()
        messagebox.showinfo("Ajout réussi", f"Le livre '{titre}' a été ajouté à la base de données.")
        refresh_table(tree)  # Rafraîchit le tableau après l'ajout
        refresh_comboboxes(titre_combobox, auteur_combobox, serie_combobox, serie_combobox_add)
    except sq.Error as e:
        messagebox.showerror("Erreur d'ajout", f"Erreur lors de l'ajout du livre : {e}")

# Fonction pour prêter un livre
def pret_livre(id_livre, nom, prenom, tree):
    try:
        date_pret = str(datetime.date.today())
        cur.execute("INSERT INTO Pret (id_livre, nom, prenom, date_pret) VALUES (?, ?, ?, ?)", (id_livre, nom.upper(), prenom.upper(), date_pret))
        connect.commit()
        messagebox.showinfo("Prêt réussi", f"Le livre avec l'ID {id_livre} a été prêté.")
        refresh_table(tree)
    except sq.Error as e:
        messagebox.showerror("Erreur de prêt", f"Erreur lors du prêt du livre : {e}")

# Fonction pour rendre un livre
def retour_livre(id_livre, tree):
    try:
        cur.execute("DELETE FROM Pret WHERE id_livre=?", (id_livre,))
        connect.commit()
        messagebox.showinfo("Retour réussi", f"Le livre avec l'ID {id_livre} a été retourné.")
        refresh_table(tree)
    except sq.Error as e:
        messagebox.showerror("Erreur de retour", f"Erreur lors du retour du livre : {e}")

# Fonction pour afficher les livres prêtés
def show_prets():
    pret_root = tk.Toplevel()
    pret_root.title("Livres prêtés")

    pret_tree = ttk.Treeview(pret_root, columns=("ID Livre", "Nom", "Prénom", "Date de prêt"), show='headings')
    pret_tree.heading("ID Livre", text="ID Livre")
    pret_tree.heading("Nom", text="Nom")
    pret_tree.heading("Prénom", text="Prénom")
    pret_tree.heading("Date de prêt", text="Date de prêt")
    pret_tree.pack(pady=10, padx=10)

    cur.execute("SELECT id_livre, nom, prenom, date_pret FROM Pret")
    for row in cur.fetchall():
        pret_tree.insert("", tk.END, values=row)

    pret_root.mainloop()

# Fonction pour rafraîchir les données dans le tableau
def refresh_table(tree, titre="", auteur="", serie="", tome=""):
    # Efface toutes les lignes actuelles du tableau
    for row in tree.get_children():
        tree.delete(row)

    # Récupère à nouveau les données depuis la base de données en fonction des critères de recherche
    rows = fetch_data(titre, auteur, serie, tome)
    for row in rows:
        tree.insert("", tk.END, values=row, tags=('prete',) if row[-1] == 1 else ('non_prete',))

    tree.tag_configure('prete', background='#FFCCCB')  # Light red
    tree.tag_configure('non_prete', background='#CCFFCC')  # Light green

# Fonction pour rafraîchir les valeurs des comboboxes
def refresh_comboboxes(titre_combobox, auteur_combobox, serie_combobox, serie_combobox_add):
    titre_combobox['values'] = fetch_unique_values("titre")
    auteur_combobox['values'] = fetch_unique_values("auteur")
    serie_combobox['values'] = fetch_unique_values("serie")
    serie_combobox_add['values'] = fetch_unique_values("serie")

# Fonction pour afficher les livres dans la fenêtre principale
def show_books():
    root = tk.Tk()
    root.title("Gestion de Bibliothèque")

    

    main_frame = tk.Frame(root)
    main_frame.pack(pady=10, padx=10)

    ascii_art = """
__________._____.   .__  .__        
\______   \__\_ |__ |  | |__| ____  
 |    |  _/  || __ \|  | |  |/  _ \ 
 |    |   \  || \_\ \  |_|  (  <_> )
 |______  /__||___  /____/__|\____/ 
        \/        \/                
"""
    ascii_label = tk.Label(main_frame, text=ascii_art, font=("Courier", 8))
    ascii_label.grid(row=0, column=0, columnspan=2)

    search_frame = tk.Frame(main_frame)
    search_frame.grid(row=1, column=0, pady=5)

    # Rechercher par titre
    tk.Label(search_frame, text="Rechercher par titre:").grid(row=0, column=0)
    titre_combobox = ttk.Combobox(search_frame, values=fetch_unique_values("titre"), width=20)
    titre_combobox.grid(row=0, column=1, padx=5)

    # Rechercher par auteur
    tk.Label(search_frame, text="Rechercher par auteur:").grid(row=0, column=2)
    auteur_combobox = ttk.Combobox(search_frame, values=fetch_unique_values("auteur"), width=20)
    auteur_combobox.grid(row=0, column=3, padx=5)

    # Rechercher par série
    tk.Label(search_frame, text="Rechercher par série:").grid(row=0, column=4)
    serie_combobox = ttk.Combobox(search_frame, values=fetch_unique_values("serie"), width=20)
    serie_combobox.grid(row=0, column=5, padx=5)

    # Rechercher par tome
    tk.Label(search_frame, text="Rechercher par tome:").grid(row=0, column=6)
    tome_entry = tk.Entry(search_frame, width=5)
    tome_entry.grid(row=0, column=7, padx=5)

    def search():
        titre = titre_combobox.get()
        auteur = auteur_combobox.get()
        serie = serie_combobox.get()
        tome = tome_entry.get()
        refresh_table(tree, titre, auteur, serie, tome)  # Rafraîchit le tableau avec les nouvelles données filtrées

    search_button = tk.Button(search_frame, text="Rechercher", command=search)
    search_button.grid(row=0, column=8, padx=5)

    tree = ttk.Treeview(main_frame, columns=("ID", "Auteur", "Date", "Titre", "Serie", "Type", "Tome", "Prêté"), show='headings', height=10)
    tree.heading("ID", text="ID")
    tree.heading("Auteur", text="Auteur")
    tree.heading("Date", text="Date d'ajout")
    tree.heading("Titre", text="Titre")
    tree.heading("Serie", text="Serie")
    tree.heading("Type", text="Type")
    tree.heading("Tome", text="Tome")
    tree.heading("Prêté", text="Prêté")
    tree.grid(row=2, column=0, padx=5, pady=5, columnspan=2)

    # Bouton pour ajouter un livre
    add_frame = tk.Frame(main_frame)
    add_frame.grid(row=3, column=0, pady=5)

    tk.Label(add_frame, text="Ajouter un livre:", font=("Arial", 10)).grid(row=0, column=0, padx=5)

    tk.Label(add_frame, text="Auteur:").grid(row=1, column=0)
    auteur_entry = tk.Entry(add_frame, width=20)
    auteur_entry.grid(row=1, column=1, padx=5)

    tk.Label(add_frame, text="Titre:").grid(row=2, column=0)
    titre_entry = tk.Entry(add_frame, width=20)
    titre_entry.grid(row=2, column=1, padx=5)

    tk.Label(add_frame, text="Série:").grid(row=3, column=0)
    serie_combobox_add = ttk.Combobox(add_frame, values=fetch_unique_values("serie"), width=20)
    serie_combobox_add.grid(row=3, column=1, padx=5)

    tk.Label(add_frame, text="Type:").grid(row=4, column=0)
    type_combobox = ttk.Combobox(add_frame, values=["BD", "ROMANS"], width=20)
    type_combobox.grid(row=4, column=1, padx=5)

    tk.Label(add_frame, text="Tome:").grid(row=5, column=0)
    tome_entry_add = tk.Entry(add_frame, width=5)
    tome_entry_add.grid(row=5, column=1, padx=5)

    def add_livre():
        auteur = auteur_entry.get()
        titre = titre_entry.get()
        serie = serie_combobox_add.get()
        type_livre = type_combobox.get()
        tome = tome_entry_add.get()
        ajout_livre(auteur, titre, serie, type_livre, tome, tree, titre_combobox, auteur_combobox, serie_combobox, serie_combobox_add)
        auteur_entry.delete(0, tk.END)
        titre_entry.delete(0, tk.END)
        serie_combobox_add.set('')
        type_combobox.set('')
        tome_entry_add.delete(0, tk.END)

    add_button = tk.Button(add_frame, text="Ajouter", command=add_livre, fg="green")
    add_button.grid(row=6, column=0, columnspan=2, pady=5)

    # Bouton pour supprimer un livre
    delete_frame = tk.Frame(main_frame)
    delete_frame.grid(row=3, column=1, pady=5)

    tk.Label(delete_frame, text="Supprimer un livre:", font=("Arial", 10)).grid(row=0, column=0, padx=5)

    tk.Label(delete_frame, text="ID du livre à supprimer:").grid(row=1, column=0)
    id_livre_entry = tk.Entry(delete_frame, width=10)
    id_livre_entry.grid(row=1, column=1, padx=5)

    def delete_livre_gui():
        id_livre = id_livre_entry.get()
        if id_livre:
            delete_livre(id_livre, tree, titre_combobox, auteur_combobox, serie_combobox, serie_combobox_add)
            id_livre_entry.delete(0, tk.END)
        else:
            messagebox.showwarning("ID manquant", "Veuillez entrer l'ID du livre à supprimer.")

    delete_button = tk.Button(delete_frame, text="Supprimer", command=delete_livre_gui, fg="red")
    delete_button.grid(row=2, column=0, columnspan=2, pady=5)

    # Bouton pour prêter un livre
    pret_frame = tk.Frame(main_frame)
    pret_frame.grid(row=4, column=0, pady=5)

    tk.Label(pret_frame, text="Prêter un livre:", font=("Arial", 10)).grid(row=0, column=0, padx=5)

    tk.Label(pret_frame, text="ID du livre:").grid(row=1, column=0)
    id_pret_entry = tk.Entry(pret_frame, width=10)
    id_pret_entry.grid(row=1, column=1, padx=5)

    tk.Label(pret_frame, text="Nom:").grid(row=2, column=0)
    nom_entry = tk.Entry(pret_frame, width=20)
    nom_entry.grid(row=2, column=1, padx=5)

    tk.Label(pret_frame, text="Prénom:").grid(row=3, column=0)
    prenom_entry = tk.Entry(pret_frame, width=20)
    prenom_entry.grid(row=3, column=1, padx=5)

    def pret_livre_gui():
        id_livre = id_pret_entry.get()
        nom = nom_entry.get()
        prenom = prenom_entry.get()
        if id_livre and nom and prenom:
            pret_livre(id_livre, nom, prenom, tree)
            id_pret_entry.delete(0, tk.END)
            nom_entry.delete(0, tk.END)
            prenom_entry.delete(0, tk.END)
        else:
            messagebox.showwarning("Information manquante", "Veuillez remplir toutes les informations pour prêter un livre.")

    pret_button = tk.Button(pret_frame, text="Prêter", command=pret_livre_gui, fg="blue")
    pret_button.grid(row=4, column=0, columnspan=2, pady=5)

    # Bouton pour retourner un livre
    retour_frame = tk.Frame(main_frame)
    retour_frame.grid(row=4, column=1, pady=5)

    tk.Label(retour_frame, text="Retourner un livre:", font=("Arial", 10)).grid(row=0, column=0, padx=5)

    tk.Label(retour_frame, text="ID du livre:").grid(row=1, column=0)
    id_retour_entry = tk.Entry(retour_frame, width=10)
    id_retour_entry.grid(row=1, column=1, padx=5)

    def retour_livre_gui():
        id_livre = id_retour_entry.get()
        if id_livre:
            retour_livre(id_livre, tree)
            id_retour_entry.delete(0, tk.END)
        else:
            messagebox.showwarning("ID manquant", "Veuillez entrer l'ID du livre à retourner.")

    retour_button = tk.Button(retour_frame, text="Retourner", command=retour_livre_gui, fg="purple")
    retour_button.grid(row=2, column=0, columnspan=2, pady=5)

    # Bouton pour afficher les livres prêtés
    pret_list_button = tk.Button(main_frame, text="Livres prêtés", command=show_prets, fg="purple")
    pret_list_button.grid(row=5, column=0, pady=5)

    refresh_table(tree)
    root.mainloop()

# Fonction principale pour démarrer l'application
if __name__ == "__main__":
    show_books()

connect.close()
