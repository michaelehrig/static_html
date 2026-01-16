from textnode import TextNode, TextType
from htmlnode import generate_pages_recursive, prepare_directory




def main():
    prepare_directory('./static','./public')
    generate_pages_recursive('./content', 'template.html', './public')

            
if __name__ == "__main__":
    main()