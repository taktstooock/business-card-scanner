import os
from typing import Dict
import re
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import google.generativeai as genai
import vobject
from dotenv import load_dotenv

class BusinessCardScanner:
    def __init__(self):
        load_dotenv()
        
        # Gemini APIの初期化
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("GOOGLE_API_KEY is not set in .env file")
            
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
    def extract_info_from_image(self, image: Image.Image) -> Dict[str, str]:
        """画像から情報を抽出する"""
        prompt = """
        Extract the following information from this business card and return it in JSON format:
        - name: Full name (in kanji, with surname and given name separated by a half-width space)
        - reading: Name reading (in full-width hiragana, with surname and given name separated by a half-width space)
        - email: Email address
        - company: Company name
        - title: Position
        - postal_code: Postal code (if not found, return an empty string)
        - address: Address (excluding the postal code)
        - phone: Phone number
        - social_links: Social media links (if there are multiple, return them as an array)
        
        If any item is not found, please use an empty string.
        """

        # prompt = """
        # この名刺から以下の情報を抽出してJSONフォーマットで返してください:
        # - name: 氏名（漢字表記・姓名の間は半角スペースで区切る）
        # - reading: 氏名の読み仮名（全角ひらがな・姓名の間は半角スペースで区切る）
        # - email: メールアドレス
        # - company: 会社名
        # - title: 役職
        # - postal_code: 郵便番号（見つからない場合は空文字列）
        # - address: 住所（郵便番号を除いた部分）
        # - phone: 電話番号
        # - social_links: SNSリンク（複数ある場合は配列で）
        
        # 見つからない項目は空文字列としてください。
        # """
        
        response = self.model.generate_content([prompt, image])
        text = response.text
        print(text)
        
        # JSON文字列を抽出して辞書に変換
        import json
        json_str = re.search(r'\{.*\}', text, re.DOTALL)
        if not json_str:
            raise ValueError("Failed to extract JSON from API response")
            
        return json.loads(json_str.group())
        
    def create_vcard(self, info: Dict[str, str], image_path: str) -> str:
        """抽出した情報からvCard文字列を作成する"""
        card = vobject.vCard()
        
        # 基本情報の設定
        name = card.add('n')
        
        # 姓名の処理
        name_parts = info['name'].split(' ', 1)
        if len(name_parts) == 2:
            last_name, first_name = name_parts
        else:
            # スペースで区切られていない場合、文字数で分割
            name_str = name_parts[0]
            middle = len(name_str) // 2
            last_name = name_str[:middle]
            first_name = name_str[middle:]
        
        name.value = vobject.vcard.Name(family=last_name, given=first_name)
        
        # 読み仮名の設定：SOUND, X-PHONETIC-LAST-NAME, X-PHONETIC-FIRST-NAMEを利用
        reading = info.get("reading", "")
        card.add('SOUND').value = reading
        reading_parts = reading.split(' ', 1)
        if len(reading_parts) == 2:
            card.add('X-PHONETIC-LAST-NAME').value = reading_parts[0]
            card.add('X-PHONETIC-FIRST-NAME').value = reading_parts[1]

        # fn（表示名）の設定
        card.add('fn').value = info["name"]
        
        # メールアドレスの設定
        if info['email']:
            email_field = card.add('email')
            email_field.value = info['email']
            email_field.type_param = "work"
            
        # その他の情報を設定
        if info['company']:
            card.add('org').value = [info['company']]
        if info['title']:
            card.add('title').value = info['title']
        # 住所設定：Geminiから取得した"postal_code"と"address"を利用
        if info.get('address') or info.get('postal_code'):
            adr = card.add('adr')
            adr.value = vobject.vcard.Address(street=info.get('address', ''), code=info.get('postal_code', ''))
        if info['phone']:
            card.add('tel').value = info['phone']
            
        # SNSリンクの設定
        if info.get('social_links'):
            for url in info['social_links']:
                card.add('url').value = url
                
        # プロフィール画像の設定
        if os.path.exists(image_path):
            import base64
            with open(image_path, 'rb') as f:
                photo_data = base64.b64encode(f.read()).decode('ascii')
            photo = card.add('photo')
            photo.value = photo_data
            photo.type_param = 'JPEG'
                
        return card.serialize()
    
    def process_pdf(self, pdf_path: str, output_dir: str):
        """PDFファイルを処理し、全連絡先のvCardをページ毎に追記して1つのファイルにまとめる"""
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, 'contacts.vcf')
        # 既存の出力ファイルの存在確認と削除確認
        if os.path.exists(output_path):
            resp = input(f"Output file '{output_path}' already exists. Delete it? (y/n): ")
            if resp.lower() == 'y':
                os.remove(output_path)
            else:
                print("Existing file retained. Data will be appended.")
        # 出力ファイルを初期化してオープン（以降、ページ毎に追記）
        with open(output_path, 'w', encoding='utf-8') as f:
            # PDFを画像に変換
            images = convert_from_path(pdf_path, poppler_path='../.library/poppler-24.02.0/Library/bin')
            for i, image in enumerate(images):
                # 画像の向き検出
                osd = pytesseract.image_to_osd(image)
                match = re.search(r'Orientation in degrees:\s*(\d+)', osd)
                if match:
                    detected_angle = int(match.group(1))
                    print(f"Detected angle: {detected_angle}")
                    if detected_angle != 0:
                        image = image.rotate(detected_angle, expand=True)
                    
                # 情報の抽出（リソース枯渇エラー時は10秒待機して再試行）
                import time
                for _ in range(10):
                    try:
                        info = self.extract_info_from_image(image)
                        break
                    except Exception as e:
                        if "Resource has been exhausted" in str(e):
                            print("Resource exhausted error encountered. Waiting 10 seconds before retrying...", end='', flush=True)
                            for _ in range(10):
                                print(".", end='', flush=True)
                                time.sleep(1)
                            print()  # 改行して再試行開始
                        else:
                            raise e
                else:
                    raise RuntimeError("Failed to extract information from image")
                            
                # 画像の一時保存（vCard用）
                temp_image_path = os.path.join(output_dir, f'card_{i}.png')
                image.save(temp_image_path)
                
                # vCard文字列を生成してファイルに追記
                vcard_text = self.create_vcard(info, temp_image_path)
                f.write(vcard_text + "\n")
                
                # 一時画像ファイルの削除
                os.remove(temp_image_path)

def main():
    scanner = BusinessCardScanner()
    
    # コマンドライン引数の処理
    import argparse
    parser = argparse.ArgumentParser(description='Convert business card PDFs to vCard files')
    parser.add_argument('pdf_path', help='Path to the PDF file containing business cards')
    parser.add_argument('--output', '-o', default='output',
                        help='Output directory for vCard files (default: output)')
    args = parser.parse_args()
    
    scanner.process_pdf(args.pdf_path, args.output)

if __name__ == '__main__':
    main()
