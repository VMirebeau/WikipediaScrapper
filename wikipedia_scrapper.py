import requests
from bs4 import BeautifulSoup, NavigableString, Tag
import re

def clean_text(texte):
    lines = texte.splitlines()
    # Supprimer les lignes vides au début
    while lines and not lines[0].strip():
        lines.pop(0)
    # Supprimer les lignes vides à la fin
    while lines and not lines[-1].strip():
        lines.pop()
    return '\n'.join(lines)


def get_text_with_inline_tags(element):
    texte = ''
    for child in element.contents:
        if isinstance(child, NavigableString):
            child_text = str(child)
            # Ajouter un espace si nécessaire, sauf si le dernier caractère est une apostrophe
            if texte and not texte[-1].isspace() and not child_text[0].isspace() and texte[-1] not in ["'", "’"]:
                texte += ' '
            texte += child_text
        elif isinstance(child, Tag):
            # Ignorer les notes de bas de page
            if child.name == 'sup' and 'reference' in child.get('class', []):
                continue
            # Ignorer les citations
            if child.name == 'a' and child.get('href') and child['href'].startswith('#cite'):
                continue
            child_text = get_text_with_inline_tags(child)
            if child_text:
                # Ajouter un espace si nécessaire, sauf si le dernier caractère est une apostrophe
                if texte and not texte[-1].isspace() and not child_text[0].isspace() and texte[-1] not in ["'", "’"]:
                    texte += ' '
                texte += child_text
    return texte



def main():
    # Demande de l'URL à l'utilisateur
    url = input("Veuillez entrer l'URL de la page Wikipedia : ")

    # Récupération du contenu de la page
    response = requests.get(url)
    if response.status_code != 200:
        print("Erreur lors de la récupération de la page.")
        return

    # Analyse du contenu HTML avec BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')

    # Extraction du titre depuis le span avec la classe "mw-page-title-main"
    titre_span = soup.find('span', class_='mw-page-title-main')
    if titre_span:
        titre = titre_span.get_text(strip=True)
    else:
        print("Erreur lors de la récupération du titre de la page.")
        return

    # Trouver le div avec id="bodyContent"
    body_content = soup.find('div', id='bodyContent')
    if not body_content:
        print("Erreur lors de la récupération du contenu principal.")
        return

    # Enlever tout ce qui précède et inclut l'infobox
    infobox = body_content.find('table', class_='infobox')
    if infobox:
        # Récupérer tous les éléments après l'infobox
        elements_after_infobox = []
        for sibling in infobox.next_siblings:
            if isinstance(sibling, (Tag, NavigableString)):
                elements_after_infobox.append(sibling)
        body_content.contents = elements_after_infobox

    # Supprimer les éléments avec la classe "bandeau-cell"
    for bandeau_cell in body_content.find_all(class_='bandeau-cell'):
        bandeau_cell.decompose()

    # Supprimer les infobox restantes
    for infobox_element in body_content.find_all(class_="infobox"):
        infobox_element.decompose()

    # Extraction du contenu à partir du premier <p> ou <h2>
    texte = ''
    started_scraping = False

    # Balises qui déclenchent l'arrêt du scraping
    stop_titles = ["Notes et références", "Références", "Bibliographie", "Voir aussi", "Liens externes"]

    for element in body_content.find_all(['p', 'li', 'h2', 'h3'], recursive=True):
        if isinstance(element, Tag):
            # Vérifier si on doit arrêter le scraping
            if element.name in ['h2', 'h3']:
                title_text = get_text_with_inline_tags(element).strip()
                if title_text in stop_titles and element.name == 'h2':
                    break  # On arrête de scrapper
                else:
                    if not started_scraping:
                        started_scraping = True
                    # Ajouter une ligne vide avant le titre et aller à la ligne après
                    texte = texte.rstrip('\n') + '\n\n' + title_text + '\n'
            elif element.name == 'p':
                if not started_scraping:
                    started_scraping = True
                paragraph_text = get_text_with_inline_tags(element)
                # Ajouter un retour à la ligne avant chaque paragraphe
                texte = texte.rstrip('\n') + '\n' + paragraph_text.strip()
            elif element.name == 'li':
                list_item_text = get_text_with_inline_tags(element)
                texte += '\n- ' + list_item_text.strip()

    # Nettoyer le texte final
    # Supprimer les espaces multiples
    texte = re.sub(r'[ \t]{2,}', ' ', texte)

    # Enlever les espaces superflus avant les signes de ponctuation simples (, .)
    texte = re.sub(r'\s+([,.])', r'\1', texte)

    # Ajouter une espace insécable avant les signes de ponctuation doubles (; : ! ?)
    texte = re.sub(r'([^\s])([;:!?])', '\\1\u00A0\\2', texte)

    # Enlever les espaces après les parenthèses ouvrantes
    texte = re.sub(r'\(\s+', '(', texte)
    # Enlever les espaces avant les parenthèses fermantes
    texte = re.sub(r'\s+\)', ')', texte)

    # Supprimer les lignes vides en début et en fin de texte
    texte = clean_text(texte)


    # Écrire le texte dans un fichier [titre].txt
    nom_fichier = f"{titre}.txt"
    with open(nom_fichier, 'w', encoding='utf-8') as fichier:
        fichier.write(texte)

    print(f"Le texte a été sauvegardé dans le fichier {nom_fichier}")

if __name__ == "__main__":
    main()
