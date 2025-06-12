#!/usr/bin/env python3

import sys
import string
import random
import qrcode
import getpass
import socket
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QRadioButton, QFrame, QGraphicsDropShadowEffect
)
from PyQt5.QtGui import QPixmap, QColor, QImage
from PyQt5.QtCore import Qt

# Impor yang diperlukan untuk menggambar di gambar
from PIL import Image, ImageDraw, ImageFont


class QRLabelWidget(QLabel):
    """Widget untuk menampilkan QR Code dengan padding."""
    def __init__(self, size=180, padding=10, parent=None):
        super().__init__(parent)
        self.size = size
        total_size = size + (padding * 2)
        self.setFixedSize(total_size, total_size)
        self.setAlignment(Qt.AlignCenter)
        self.setObjectName("qrContainer")

    def set_qr_data(self, data):
        """Membuat dan menampilkan QR code dari data yang diberikan."""
        if not data:
            self.clear()
            return

        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_Q,
            box_size=4,
            border=4
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        img_pil = qr.make_image(fill_color="#1F1F1F", back_color="white").convert('RGBA')
        raw_data = img_pil.tobytes("raw", "RGBA")
        qimage = QImage(raw_data, img_pil.size[0], img_pil.size[1], QImage.Format_RGBA8888)
        pixmap = QPixmap.fromImage(qimage)

        scaled_pixmap = pixmap.scaled(self.size, self.size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.setPixmap(scaled_pixmap)


class PasswordCard(QWidget):
    """UI utama yang berbentuk seperti kartu password."""
    WINDOW_HEIGHT = 620
    WINDOW_WIDTH = 420

    STYLE_SHEET = """
        #mainCard {
            background-color: #FDFDFD;
            border-radius: 20px;
        }
        #qrContainer {
            background-color: white;
            border: 1px solid #E0E0E0;
            border-radius: 12px;
        }
        QLabel {
            color: #333;
            font-family: 'Segoe UI', 'Arial';
            font-size: 14px;
        }
        #titleLabel {
            font-size: 24px;
            font-weight: bold;
            color: #222;
        }
        #subtitleLabel {
            font-size: 13px;
            color: #777;
        }
        QRadioButton {
            color: #555;
            font-family: 'Segoe UI', 'Arial';
            font-size: 14px;
            padding: 5px 0;
        }
        QLineEdit {
            background-color: #FFFFFF;
            border: 1px solid #CFD8DC;
            border-radius: 8px;
            padding: 8px 12px;
            font-family: 'Segoe UI', 'Arial';
            font-size: 14px;
            color: #333;
        }
        QLineEdit:read-only {
            background-color: #ECEFF1;
            color: #546E7A;
            border-color: #B0BEC5;
        }
        QLineEdit:focus {
            border: 1px solid #007BFF;
        }
        #closeButton {
            background-color: transparent;
            color: #aaa;
            border: none;
            font-size: 22px;
            font-weight: bold;
        }
        #closeButton:hover { color: #333; }
        #actionButton {
            background-color: #007BFF;
            color: white;
            font-weight: bold;
            border: none;
            border-radius: 8px;
            padding: 10px 16px;
            font-family: 'Segoe UI', 'Arial';
            font-size: 14px;
        }
        #actionButton:pressed { background-color: #0056b3; }
        #refreshButton {
            background-color: #E0E0E0;
            color: #333;
            border: none;
            border-radius: 8px;
            font-size: 20px;
            font-weight: bold;
            min-width: 40px;
        }
        #refreshButton:hover { background-color: #D0D0D0; }
        #refreshButton:pressed { background-color: #C0C0C0; }
    """

    def __init__(self):
        super().__init__()
        self._full_random_password = ""
        self.drag_pos = None
        self.init_ui()
        self.generate_and_display_random()


    def init_ui(self):
        self._setup_window()
        self._create_widgets()
        self._setup_layouts()
        self._connect_signals()
        self._apply_styles()

    def _setup_window(self):
        self.setWindowTitle("Password Card")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(self.WINDOW_WIDTH, self.WINDOW_HEIGHT)

    def _create_widgets(self):
        self.card_frame = QFrame(self)
        self.card_frame.setObjectName("mainCard")
        self._apply_shadow_effect(self.card_frame)

        self.close_button = QPushButton("✕")
        self.close_button.setObjectName("closeButton")

        try:
            current_user = getpass.getuser()
            hostname = socket.gethostname()
        except Exception:
            current_user = "user"
            hostname = "computer"
        self.title_label = QLabel(current_user)
        self.title_label.setObjectName("titleLabel")
        self.subtitle_label = QLabel(hostname)
        self.subtitle_label.setObjectName("subtitleLabel")

        self.qr_widget_display = QRLabelWidget()
        self.manual_radio = QRadioButton("Manual Password")
        self.automatic_radio = QRadioButton("Automatic Password")
        self.automatic_radio.setChecked(True)
        self.current_pass_input = self._create_input_field(QLineEdit.Password)
        self.current_pass_row = self._create_form_row("Current", self.current_pass_input)
        self.new_pass_input = self._create_input_field(QLineEdit.Password)
        self.new_pass_row = self._create_form_row("New", self.new_pass_input)
        self.confirmation_input = self._create_input_field(QLineEdit.Password)
        self.confirmation_row = self._create_form_row("Confirm", self.confirmation_input)
        self.random_pass_display = self._create_input_field(is_readonly=True)
        self.refresh_button = QPushButton("↻")
        self.refresh_button.setObjectName("refreshButton")
        self.random_pass_row = self._create_form_row("Random", self.random_pass_display, self.refresh_button)
        self.action_button = QPushButton("Update QR Code")
        self.action_button.setObjectName("actionButton")

    def _setup_layouts(self):
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.card_frame)
        card_content_layout = QVBoxLayout(self.card_frame)
        card_content_layout.setContentsMargins(25, 20, 25, 25)
        card_content_layout.setSpacing(15)
        top_bar_layout = QHBoxLayout()
        title_layout = QVBoxLayout()
        title_layout.setSpacing(0)
        title_layout.addWidget(self.title_label)
        title_layout.addWidget(self.subtitle_label)
        top_bar_layout.addLayout(title_layout)
        top_bar_layout.addStretch()
        top_bar_layout.addWidget(self.close_button, alignment=Qt.AlignTop)
        card_content_layout.addLayout(top_bar_layout)
        card_content_layout.addWidget(self.qr_widget_display, alignment=Qt.AlignCenter)
        radio_layout = QHBoxLayout()
        radio_layout.addStretch()
        radio_layout.addWidget(self.manual_radio)
        radio_layout.addWidget(self.automatic_radio)
        radio_layout.addStretch()
        card_content_layout.addLayout(radio_layout)
        form_layout = QVBoxLayout()
        form_layout.setSpacing(10)
        form_layout.addWidget(self.current_pass_row)
        form_layout.addWidget(self.new_pass_row)
        form_layout.addWidget(self.confirmation_row)
        form_layout.addWidget(self.random_pass_row)
        card_content_layout.addLayout(form_layout)
        card_content_layout.addStretch(1)
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.action_button)
        button_layout.addStretch()
        card_content_layout.addLayout(button_layout)
        self.update_form_view()

    def _connect_signals(self):
        self.close_button.clicked.connect(self.close)
        self.automatic_radio.toggled.connect(self.update_form_view)
        self.action_button.clicked.connect(self.process_password)
        self.refresh_button.clicked.connect(self.generate_and_display_random)

    def _apply_styles(self):
        self.setStyleSheet(self.STYLE_SHEET)

    def _apply_shadow_effect(self, widget):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setXOffset(0)
        shadow.setYOffset(5)
        shadow.setColor(QColor(0, 0, 0, 30))
        widget.setGraphicsEffect(shadow)
        
    def update_form_view(self):
        is_auto = self.automatic_radio.isChecked()
        self.new_pass_row.setVisible(not is_auto)
        self.confirmation_row.setVisible(not is_auto)
        self.random_pass_row.setVisible(is_auto)

    # --- FUNGSI YANG DIMODIFIKASI ---
    def process_password(self):
        final_password = ""
        if self.automatic_radio.isChecked():
            final_password = self._full_random_password
        else:
            new_pass = self.new_pass_input.text()
            conf_pass = self.confirmation_input.text()
            if not new_pass or not conf_pass:
                print("Field 'New password' dan 'Confirmation' tidak boleh kosong.")
                return
            if new_pass != conf_pass:
                print("Error: 'New password' dan 'Confirmation' tidak cocok!")
                return
            final_password = new_pass

        self.qr_widget_display.set_qr_data(final_password)
        print(f"Password diatur ke: '{final_password}'")
        
        try:
            card_background = Image.open("card.png").convert("RGBA")
            card_width, card_height = card_background.size
            draw = ImageDraw.Draw(card_background)

            username = self.title_label.text()
            hostname = self.subtitle_label.text()
            combined_text = f"{username}@{hostname}"
            
            # --- PENYESUAIAN FONT ---
            # Ukuran font ditingkatkan menjadi 58 untuk membuatnya lebih besar dan bold.
            try:
                main_font = ImageFont.truetype("arialbd.ttf", 78)
            except IOError:
                print("Font Arial Bold tidak ditemukan, menggunakan font default.")
                main_font = ImageFont.load_default()

            bbox_text = draw.textbbox((0, 0), combined_text, font=main_font)
            text_width = bbox_text[2] - bbox_text[0]
            text_pos_x = (card_width - text_width) // 2
            text_pos_y = 45
            draw.text((text_pos_x, text_pos_y), combined_text, font=main_font, fill="#FFFFFF")

            qr = qrcode.QRCode(
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=4,
            )
            qr.add_data(final_password)
            qr.make(fit=True)
            qr_image = qr.make_image(fill_color="black", back_color="white").convert('RGBA')

            # --- PENYESUAIAN UKURAN QR CODE ---
            # Ukuran QR code dikecilkan menjadi 260x260 piksel.
            qr_size = 200
            qr_image_resized = qr_image.resize((qr_size, qr_size), Image.LANCZOS)
            
            qr_pos_x = (card_width - qr_size) // 2
            qr_pos_y = text_pos_y + (bbox_text[3] - bbox_text[1]) + 10 # Menambah jarak vertikal
            
            card_background.paste(qr_image_resized, (qr_pos_x, qr_pos_y), qr_image_resized)
            
            # Mengubah nama file output agar tidak menimpa hasil sebelumnya
            output_filename = "kartu_hasil_terbaru.png"
            card_background.save(output_filename)
            print(f"Kartu berhasil diperbarui dan disimpan sebagai '{output_filename}'")

        except FileNotFoundError:
            print(f"\nError: File 'card.png' tidak ditemukan. Pastikan file tersebut ada di folder yang sama.")
        except Exception as e:
            print(f"Terjadi error saat membuat gambar kartu: {e}")

        self.new_pass_input.clear()
        self.confirmation_input.clear()


    def generate_and_display_random(self):
        self._full_random_password = self._generate_password()
        obscured_pass = f"{self._full_random_password[:3]}••••{self._full_random_password[-4:]}"
        self.random_pass_display.setText(obscured_pass)
        
        if self.automatic_radio.isChecked():
            self.qr_widget_display.set_qr_data(self._full_random_password)

    def _create_input_field(self, mode=QLineEdit.Normal, is_readonly=False):
        line_edit = QLineEdit()
        line_edit.setEchoMode(mode)
        line_edit.setReadOnly(is_readonly)
        return line_edit

    def _create_form_row(self, label_text, widget, extra_widget=None):
        row = QFrame()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        label = QLabel(label_text)
        label.setFixedWidth(80)
        layout.addWidget(label)
        layout.addWidget(widget)
        
        if extra_widget:
            layout.setSpacing(10)
            layout.addWidget(extra_widget)
        return row

    def _generate_password(self, length=16):
        chars = string.ascii_letters + string.digits + "!@#$%^&*()"
        return ''.join(random.choice(chars) for _ in range(length))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.drag_pos:
            self.move(event.globalPos() - self.drag_pos)
            event.accept()


def main():
    app = QApplication(sys.argv)
    manager = PasswordCard()
    manager.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()