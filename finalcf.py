from PIL import Image, ImageDraw, ImageFont
import os

def create_certificate(template_path, output_folder, names, font_path, font_size=50, text_color=(0, 0, 0), x_offset=0, y_offset=0):
    if not isinstance(font_size, int):
        raise TypeError("Font size must be an integer.")

    if not os.path.isfile(template_path):
        raise FileNotFoundError(f"Template image '{template_path}' not found.")

    if not os.path.isfile(font_path):
        raise FileNotFoundError(f"Font file '{font_path}' not found.")
    
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for name in names:
        try:
            # Start with the initial font size for each certificate
            current_font_size = font_size
            image = Image.open(template_path)
            draw = ImageDraw.Draw(image)

            # Load the font and adjust the size if necessary
            font = ImageFont.truetype(font_path, current_font_size)
            text_bbox = draw.textbbox((0, 0), name, font=font)
            text_width, text_height = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]
            image_width, image_height = image.size

            # Adjust font size if the text is too wide for the image
            while text_width > image_width - 40:
                current_font_size -= 1
                font = ImageFont.truetype(font_path, current_font_size)
                text_bbox = draw.textbbox((0, 0), name, font=font)
                text_width = text_bbox[2] - text_bbox[0]

            # Center the text on the image
            x = (image_width - text_width) // 2 + x_offset
            y = (image_height - text_height) // 2 + y_offset

            # Draw the name on the certificate
            draw.text((x, y), name, font=font, fill=text_color)

            # Save the certificate
            output_path = os.path.join(output_folder, f"{name.replace(' ', '_')}.png")
            image.save(output_path)
            print(f"Saved certificate for {name} as {output_path}")

        except Exception as e:
            print(f"An error occurred while generating certificate for {name}: {e}")

# Paths and settings
template_image = 'N:\conceit-certii\participant.png'
output_dir = 'Certi'
font_file = 'N:\conceit-certii\Font Files\Poppins-Bold.ttf'
font_size = 70
text_color = (0, 0, 0)
x_offset = 0  # Adjust this to move left/right
y_offset = -10  # Adjust this to move up/down

# List of specific names to generate certificates for
# List of specific names to generate certificates for
names_list = [
  "Urmil Paneliya",
  "Patel Yaksh Birenkumar",
  "Misty Sandipkumar Patel",
  "Suthar vedant kalpeshbhai",
  "Vrund Chiragkumar Patel",
  "Chavda Rajvirsinh Dilavarsinh",
  "Denil Rupeshbhai Patel",
  "Siddh Patel",
  "Patel Krisha Nimeshkumar",
  "Parmar Vignesh Kishorbhai",
  "Baria smit",
  "Dhvij Jatinkumar Rami",
  "PAREKH SHREY HEMAL",
  "Neel Ganeshbhai Patel",
  "Solanki KaivalKumar Chandubhai",
  "Padhiyar Kuldipsinh Shaileshbhai",
  "Kaival Parekh",
  "PRINCY PRAJAPATI",
  "Lavya Dharmesh Bharada",
  "KRISHA NIMESHKUMAR PATEL",
  "Moumita Pal",
  "Aryan Mahendra Purabiya",
  "GOKANI KRISH TAPUBHAI",
  "PARV PANCHAL CHETANBHAI",
  "Pratvi Suthar",
  "Yashvi Dave",
  "Desai Purva Vijaybhai",
  "Tejas patel",
  "Patel vruti kishorkumar",
  "Shah Krisha girish",
  "Anjali Tripathi",
  "Hir Maurya",
  "Shaishavi Panchal",
  "Aanya Patel",
  "Daksh Chaklasiya",
  "Vidisha Mistry",
  "Tirth Mistry",
  "Patel Vrajkumar Amitkumar",
  "Tia Patel",
  "Vraj Panchal",
  "Shrey hirenkumar dalwadi",
  "Soumyajit Das",
  "Dhara Rajeshbhai prajapati",
  "Prisha Patel",
  "Shraddha Zala",
  "Tanashvi Bhatti",
  "Shreya Khacharia",
  "Shlok Parmar",
  "Shraddha Prajapati",
  "Yasminkhatun Sekh",
  "Kruparani Tomar",
  "Smit Chudasama",
  "Yash Patel",
  "Akshar Chauhan",
  "Vruti Patel",
  "Tejas Patel",
  "Shyam Patel",
  "Ronak Das",
  "Tithi Bhatt",
  "Krisha Shah",
  "Yashvi Dave"
]
try:
    create_certificate(template_image, output_dir, names_list, font_file, font_size, text_color, x_offset, y_offset)
except Exception as e:
    print(f"An error occurred: {e}")