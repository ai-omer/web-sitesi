"""
Mervenin Mutfagi - Gemini AI Servisi
Tarif uretimi ve prompt muhendisligi.
google.genai (yeni SDK) kullanilmaktadir.
"""

import os
import json
import time
import re
import logging
from typing import Optional

logger = logging.getLogger("mervenin_mutfagi.gemini")

try:
    from google import genai as google_genai
    from google.genai import types as genai_types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("google-genai kutuphane bulunamadi. Lutfen pip install google-genai calistirin.")


class GeminiService:
    """Google Gemini API ile tarif uretimi servisi."""

    MODEL_NAME = "gemini-3.1-flash-lite"

    def __init__(self):
        self.client = None
        self.api_key_configured = False
        self._initialize()

    def _initialize(self):
        """API anahtarini ortam degiskeninden yukler, istemciyi baslatir."""
        if not GEMINI_AVAILABLE:
            logger.error("Gemini kutuphane yuklu degil.")
            return

        api_key = os.getenv("GEMINI_API_KEY", "").strip()

        if not api_key or api_key == "your_gemini_api_key_here":
            logger.warning(
                "GEMINI_API_KEY tanimlanmamis veya varsayilan degerde. "
                "Lutfen backend/.env dosyasini duzenleyin."
            )
            return

        try:
            self.client = google_genai.Client(api_key=api_key)
            self.api_key_configured = True
            logger.info("Gemini istemcisi basariyla baslatildi: %s", self.MODEL_NAME)
        except Exception as exc:
            logger.error("Gemini baslatma hatasi: %s", exc)

    def _build_prompt(
        self,
        ingredients: list,
        cuisine: str,
    ) -> str:
        """Structured prompt olusturur."""
        ingredients_str = ", ".join(ingredients)

        return f"""Sen "Mervenin Mutfağı" platformunun şefi Merve olarak çalışıyorsun.
Sana verilen malzemeleri kullanarak {cuisine} kültüründen ilham alan 3 farklı tarif seçeneği oluştur:
1. "pratik": En fazla 15-20 dakikada hızlıca hazırlanabilecek pratik bir seçenek.
2. "geleneksel": {cuisine} mutfağının o yöresine ait, aslına sadık kalınmış geleneksel bir öneri.
3. "yaratici": Malzemeleri ezber dışı, daha değişik ve gurme fikirlerle harmanlayan yaratıcı bir şef önerisi.

Malzemeler: {ingredients_str}
Seçilen Mutfak: {cuisine}

ÖNEMLİ DETAY VE ANLATIM TALİMATLARI:
- "malzemeler_detay": Her tarif için hangi malzemenin ne kadar (örn: 2 adet orta boy domates, 1 yemek kaşığı sızma zeytinyağı, 1/2 çay kaşığı taze çekilmiş karabiber) kullanılacağını belirten son derece detaylı ve ölçülü bir malzeme listesi hazırlamalısın.
- "hazirlanis_adimlari": Yemeğin yapılışını, kullanılan profesyonel teknikleri, ocağın ateş derecesini ve ince detaylarını adım adım detaylı anlatan bir dizi (array). Her adım en az 2-3 cümle olmalıdır. Dereceler, süreler, kıvam tanımları (örn: kulak memesi kıvamı, yoğurt kıvamı, pürüzsüz olana kadar vb.) mutlaka belirtilmelidir.
- "puf_noktalari": Merve Şef'in ağzından yazılmış (samimi, sıcak ve profesyonel bir influencer tonunda), yemeğin lezzetini katlayacak en az 2-3 adet profesyonel tüyo ve püf noktası içermelidir (örn. etin mühürlenmesi, sosun kesilmemesi için püf noktaları, baharatların ekleneceği ideal anlar, dinlendirme süreleri vb.).
- "sunum_onerisi": Yemeğin tabaklanması ve influencer tarzında sosyal medyada şık görünmesi için estetik, iştah açıcı ve modern bir sunum tavsiyesi.

Yanıtını MUTLAKA aşağıdaki JSON formatında ver. Başka hiçbir şey yazma, sadece JSON:

{{
  "cuisine": "{cuisine}",
  "pratik": {{
    "title": "Pratik Tarif Adı",
    "description": "Tarifi anlatan kısa ve iştah açıcı 1-2 cümlelik açıklama",
    "servings": "Kaç kişilik",
    "prep_time": "Hazırlık süresi (örn: 5 dakika)",
    "cook_time": "Pişirme süresi (örn: 10 dakika)",
    "total_time": "Toplam süre (örn: 15 dakika)",
    "difficulty": "Kolay / Orta / Zor",
    "ingredients_used": ["kullanılan temel malzeme 1", "kullanılan temel malzeme 2"],
    "additional_ingredients": ["ekstra öneri 1", "ekstra öneri 2"],
    "malzemeler_detay": [
      "Kullanılan her malzemenin miktarıyla (örn: 2 adet domates, 1 tatlı kaşığı tuz) detaylı listesi...",
      "Diğer detaylı malzeme miktarı ile..."
    ],
    "hazirlanis_adimlari": [
      "İlk hazırlık adımı: Malzemelerin doğrama şekli, yıkanması ve ön hazırlığı hakkında en az 2-3 cümleden oluşan detaylı şef anlatımı...",
      "Isı ayarı, pişirme kabı seçimi, ilk sotelenecek malzemelerin soteleme süresi ve tekniği hakkında en az 2-3 cümleden oluşan detaylı şef anlatımı...",
      "Son pişirme/fırınlama ayarları, yemeğin piştiğini gösteren görsel/fiziksel belirtiler hakkında en az 2-3 cümleden oluşan detaylı şef anlatımı..."
    ],
    "puf_noktalari": [
      "Merve Şef'in ağzından yazılmış, lezzeti katlayacak 1. püf noktası veya tüyo...",
      "Merve Şef'in ağzından yazılmış 2. püf noktası veya tüyo...",
      "Merve Şef'in ağzından yazılmış 3. püf noktası veya tüyo..."
    ],
    "sunum_onerisi": "Yemeğin tabaklanması, influencer tarzında estetik ve şık görünmesi için sunum tavsiyesi...",
    "steps": [
      {{"step_number": 1, "description": "hazirlanis_adimlari dizisindeki ilk adımın özeti veya aynısı..."}},
      {{"step_number": 2, "description": "hazirlanis_adimlari dizisindeki ikinci adımın özeti veya aynısı..."}}
    ],
    "tips": [
      "puf_noktalari dizisindeki ilk tüyolar..."
    ],
    "nutrition": {{
      "calories": "tahmini kalori",
      "protein": "protein miktarı",
      "carbs": "karbonhidrat miktarı",
      "fat": "yağ miktarı"
    }}
  }},
  "geleneksel": {{
    "title": "Geleneksel Tarif Adı",
    "description": "Tarifi anlatan kısa ve iştah açıcı 1-2 cümlelik açıklama",
    "servings": "Kaç kişilik",
    "prep_time": "Hazırlık süresi",
    "cook_time": "Pişirme süresi",
    "total_time": "Toplam süre",
    "difficulty": "Kolay / Orta / Zor",
    "ingredients_used": ["kullanılan temel malzeme 1"],
    "additional_ingredients": ["ekstra öneri 1"],
    "malzemeler_detay": [
      "Miktarıyla birlikte detaylı malzeme..."
    ],
    "hazirlanis_adimlari": [
      "Geleneksel ön hazırlık ve marine etme gibi detayları içeren en az 2-3 cümleden oluşan detaylı adım...",
      "Geleneksel pişirme kabı (örn: toprak güveç) seçimi, ısı ayarı ve pişirme süresini içeren en az 2-3 cümleden oluşan detaylı adım..."
    ],
    "puf_noktalari": [
      "Otantik geleneksel lezzeti yakalamak için Merve Şef'in 1. püf noktası...",
      "Kıvamı mükemmelleştirecek 2. püf noktası..."
    ],
    "sunum_onerisi": "Geleneksel sunum şekli ve şık tabaklama tüyosu...",
    "steps": [
      {{"step_number": 1, "description": "hazirlanis_adimlari dizisindeki ilk adımın özeti veya aynısı..."}}
    ],
    "tips": [
      "puf_noktalari dizisindeki tüyolar..."
    ],
    "nutrition": {{
      "calories": "tahmini kalori",
      "protein": "protein miktarı",
      "carbs": "karbonhidrat miktarı",
      "fat": "yağ miktarı"
    }}
  }},
  "yaratici": {{
    "title": "Yaratıcı Tarif Adı",
    "description": "Tarifi anlatan kısa ve iştah açıcı 1-2 cümlelik açıklama",
    "servings": "Kaç kişilik",
    "prep_time": "Hazırlık süresi",
    "cook_time": "Pişirme süresi",
    "total_time": "Toplam süre",
    "difficulty": "Kolay / Orta / Zor",
    "ingredients_used": ["kullanılan temel malzeme 1"],
    "additional_ingredients": ["ekstra öneri 1"],
    "malzemeler_detay": [
      "Miktarıyla birlikte detaylı malzeme..."
    ],
    "hazirlanis_adimlari": [
      "Ezber dışı hazırlık ve sıradışı teknikleri içeren en az 2-3 cümleden oluşan detaylı adım...",
      "Yaratıcı sosların bir araya gelişi ve dokusal kontrast tekniklerini içeren en az 2-3 cümleden oluşan detaylı adım..."
    ],
    "puf_noktalari": [
      "Modern dokunuşlar ve şık çıtırlıklar için Merve Şef'in 1. yaratıcı püf noktası...",
      "Sıradışı lezzet uyumları için 2. yaratıcı püf noktası..."
    ],
    "sunum_onerisi": "Modern gurme tabaklama ve şık influencer sunum önerisi...",
    "steps": [
      {{"step_number": 1, "description": "hazirlanis_adimlari dizisindeki ilk adımın özeti veya aynısı..."}}
    ],
    "tips": [
      "puf_noktalari dizisindeki tüyolar..."
    ],
    "nutrition": {{
      "calories": "tahmini kalori",
      "protein": "protein miktarı",
      "carbs": "karbonhidrat miktarı",
      "fat": "yağ miktarı"
    }}
  }}
}}"""

    def _parse_response(self, raw_text: str) -> dict:
        """
        AI yanitindan JSON cikarir.
        Birden fazla fallback mekanizmasi ile kirilmaz yapi saglar.
        """
        cleaned = raw_text.strip()

        # 1. Dogrudan JSON parse dene
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        # 2. Markdown kod blogunu veya ilk JSON nesnesini bul
        patterns = [
            r"```json\s*([\s\S]*?)\s*```",
            r"```\s*([\s\S]*?)\s*```",
            r"(\{[\s\S]*\})",
        ]
        for pattern in patterns:
            match = re.search(pattern, cleaned, re.DOTALL)
            if match:
                candidate = match.group(1).strip()
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    continue

        # 3. Tum denemeler basarisiz - bos / fallback yapisi dondur
        logger.warning("JSON parse basarisiz, bos uc uclu yapi olusturuluyor.")
        fallback_recipe = {
            "title": "Merve Şef Özel Önerisi",
            "description": "Yazı formatında üretilen tarif.",
            "steps": [{"step_number": 1, "description": raw_text}],
            "tips": [],
            "malzemeler_detay": [],
            "hazirlanis_adimlari": [raw_text],
            "puf_noktalari": [],
            "sunum_onerisi": ""
        }
        return {
            "pratik": fallback_recipe,
            "geleneksel": fallback_recipe,
            "yaratici": fallback_recipe,
        }

    def _build_direct_prompt(
        self,
        dish_name: str,
    ) -> str:
        """Doğrudan yemek adı için prompt oluşturur."""
        return f"""Sen "Mervenin Mutfağı" platformunun şefi Merve olarak çalışıyorsun.
Senden istenen "{dish_name}" yemeğinin aslına sadık kalınmış, son derece detaylı ve profesyonel tarifini hazırlamanı istiyorum.

Yemek Adı: {dish_name}

ÖNEMLİ DETAY VE ANLATIM TALİMATLARI:
- "title": Yemeğin tam adı (örn: "Geleneksel Kuru Fasulye").
- "description": Tarifi anlatan kısa ve iştah açıcı 1-2 cümlelik açıklama.
- "cuisine": Bu yemeğin ait olduğu mutfak kültürü (örn: "Türk Mutfağı", "İtalyan Mutfağı").
- "difficulty": Kolay / Orta / Zor.
- "servings": Kaç kişilik.
- "prep_time": Hazırlık süresi (örn: 10 dakika).
- "cook_time": Pişirme süresi (örn: 40 dakika).
- "total_time": Toplam süre (örn: 50 dakika).
- "ingredients_used": Tarifteki ana malzemelerin basit listesi.
- "additional_ingredients": Varsa bu yemeğin yanına yakışacak garnitür, servis elemanları veya ekstra önerilen malzemeler.
- "malzemeler_detay": Hangi malzemenin ne kadar (örn: 2 su bardağı kuru fasulye, 1 adet kuru soğan, 1 yemek kaşığı tereyağı vb.) kullanılacağını belirten son derece detaylı ve ölçülü bir malzeme listesi.
- "hazirlanis_adimlari": Yemeğin yapılışını adım adım detaylı anlatan bir dizi (array). Her adım en az 2-3 cümle olmalıdır. Sıcaklıklar, süreler, kıvam tanımları mutlaka belirtilmelidir.
- "puf_noktalari": Merve Şef'in ağzından yazılmış (samimi, sıcak ve profesyonel bir influencer tonunda), yemeğin lezzetini katlayacak en az 2-3 adet profesyonel tüyo ve püf noktası.
- "sunum_onerisi": Yemeğin tabaklanması ve influencer tarzında sosyal medyada şık görünmesi için estetik, iştah açıcı ve modern bir sunum tavsiyesi.
- "nutrition": Kalori ve makro değerleri (tahmini).

Yanıtını MUTLAKA aşağıdaki JSON formatında ver. Başka hiçbir şey yazma, sadece JSON:

{{
  "title": "Geleneksel Kuru Fasulye",
  "description": "Kıvamı koyu, tereyağı kokulu, tam ölçülü geleneksel kuru fasulye tarifi.",
  "cuisine": "Türk Mutfağı",
  "servings": "4 Kişilik",
  "prep_time": "15 dakika",
  "cook_time": "40 dakika",
  "total_time": "55 dakika",
  "difficulty": "Orta",
  "ingredients_used": ["kuru fasulye", "soğan", "tereyağı", "salça"],
  "additional_ingredients": ["pilav", "turşu"],
  "malzemeler_detay": [
    "2 su bardağı kuru fasulye (akşamdan ıslatılmış)",
    "1 adet orta boy kuru soğan",
    "2 yemek kaşığı tereyağı",
    "1 yemek kaşığı biber salçası"
  ],
  "hazirlanis_adimlari": [
    "Akşamdan ıslattığınız fasulyeleri yıkayıp süzün ve üzerini geçecek kadar temiz suyla tencereye alarak hafifçe yumuşayana kadar yaklaşık 15-20 dakika haşlayıp köpüklerini süzün.",
    "Ayrı bir tencerede tereyağını eritin, yemeklik doğranmış soğanları ekleyip pembeleşene kadar orta ateşte soteleyin. Ardından salçayı ekleyip kokusu çıkana kadar kavurun.",
    "Haşlanıp süzülen fasulyeleri tencereye ilave edin. Üzerini 2 parmak geçecek şekilde sıcak su ekleyin ve kısık ateşte fasulyeler helmelenip lokum kıvamına gelene kadar yaklaşık 35-40 dakika pişirin."
  ],
  "puf_noktalari": [
    "Fasulyelerin gaz yapmaması ve kolay pişmesi için mutlaka akşamdan oda sıcaklığındaki içme suyunda ıslatın.",
    "Yemeğin kıvamının koyu (helmelenmiş) olması için pişme süresinin son 10 dakikasında tencerenin kapağını hafif açık bırakarak kısık ateşte kaynatın."
  ],
  "sunum_onerisi": "Yanına tane tane dökülen tereyağlı pirinç pilavı ve çıtır bir ev turşusu ile servis edebilirsiniz.",
  "nutrition": {{
    "calories": "320 kcal",
    "protein": "12g",
    "carbs": "45g",
    "fat": "8g"
  }}
}}

Aşağıda istenen yemeğin bilgilerini doldurarak sadece JSON olarak dön:

dish_name: {dish_name}"""

    def _parse_direct_response(self, raw_text: str) -> dict:
        """
        AI yanitindan tek bir tarifi JSON olarak cikarir.
        """
        cleaned = raw_text.strip()

        # 1. Dogrudan JSON parse dene
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        # 2. Markdown kod blogunu veya ilk JSON nesnesini bul
        patterns = [
            r"```json\s*([\s\S]*?)\s*```",
            r"```\s*([\s\S]*?)\s*```",
            r"(\{[\s\S]*\})",
        ]
        for pattern in patterns:
            match = re.search(pattern, cleaned, re.DOTALL)
            if match:
                candidate = match.group(1).strip()
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    continue

        # 3. Fallback
        return {
            "title": "Merve Şef Özel Tarifi",
            "description": "Yazı formatında üretilen tarif.",
            "malzemeler_detay": [],
            "hazirlanis_adimlari": [raw_text],
            "puf_noktalari": [],
            "sunum_onerisi": "",
            "nutrition": {}
        }

    async def generate_recipe(
        self,
        ingredients: list,
        cuisine: str = "Türk Mutfağı",
    ) -> dict:
        """
        Tarif uretir. Her hata durumunda anlamli bir yanit doner,
        asla exception firlatmaz.
        """
        start_time = time.time()

        if not self.api_key_configured or self.client is None:
            return {
                "success": False,
                "error": "api_key_missing",
                "message": (
                    "API anahtari yapilandirilmamis. "
                    "Lutfen backend/.env dosyasina GEMINI_API_KEY ekleyin."
                ),
            }

        prompt = self._build_prompt(ingredients, cuisine)

        try:
            response = self.client.models.generate_content(
                model=self.MODEL_NAME,
                contents=prompt,
                config=genai_types.GenerateContentConfig(
                    temperature=0.8,
                    top_p=0.95,
                    top_k=40,
                    max_output_tokens=4096,
                ),
            )

            raw_text = response.text if hasattr(response, "text") else str(response)
            parsed = self._parse_response(raw_text)
            elapsed_ms = round((time.time() - start_time) * 1000, 2)

            return {
                "success": True,
                "elapsed_ms": elapsed_ms,
                **parsed,
            }

        except Exception as exc:
            elapsed_ms = round((time.time() - start_time) * 1000, 2)
            error_str = str(exc)
            logger.error("Gemini API hatasi (%sms): %s", elapsed_ms, error_str)

            if "API_KEY_INVALID" in error_str or "api key" in error_str.lower():
                user_message = "API anahtari gecersiz. Lutfen .env dosyasindaki anahtari kontrol edin."
            elif "quota" in error_str.lower() or "429" in error_str:
                user_message = "Gunluk tarif limitine ulasildi. Lutfen biraz sonra tekrar deneyin."
            elif "timeout" in error_str.lower():
                user_message = "Baglanti zaman asimina ugradi. Lutfen tekrar deneyin."
            else:
                user_message = "Tarif olusturulurken beklenmeyen bir hata olustu. Lutfen tekrar deneyin."

            return {
                "success": False,
                "error": "generation_failed",
                "message": user_message,
                "detail": error_str,
                "elapsed_ms": elapsed_ms,
            }

    async def generate_direct_recipe(
        self,
        dish_name: str,
        language: str = "tr",
    ) -> dict:
        """Doğrudan yemek adına göre tarif üretir."""
        start_time = time.time()

        if not self.api_key_configured or self.client is None:
            return {
                "success": False,
                "error": "api_key_missing",
                "message": (
                    "API anahtari yapilandirilmamis. "
                    "Lutfen backend/.env dosyasina GEMINI_API_KEY ekleyin."
                ),
            }

        prompt = self._build_direct_prompt(dish_name)

        try:
            response = self.client.models.generate_content(
                model=self.MODEL_NAME,
                contents=prompt,
                config=genai_types.GenerateContentConfig(
                    temperature=0.7,
                    top_p=0.95,
                    top_k=40,
                    max_output_tokens=4096,
                ),
            )

            raw_text = response.text if hasattr(response, "text") else str(response)
            parsed = self._parse_direct_response(raw_text)
            elapsed_ms = round((time.time() - start_time) * 1000, 2)

            return {
                "success": True,
                "elapsed_ms": elapsed_ms,
                "recipe": parsed,
            }

        except Exception as exc:
            elapsed_ms = round((time.time() - start_time) * 1000, 2)
            error_str = str(exc)
            logger.error("Gemini API direct recipe hatasi (%sms): %s", elapsed_ms, error_str)

            if "API_KEY_INVALID" in error_str or "api key" in error_str.lower():
                user_message = "API anahtari gecersiz. Lutfen .env dosyasindaki anahtari kontrol edin."
            elif "quota" in error_str.lower() or "429" in error_str:
                user_message = "Gunluk tarif limitine ulasildi. Lutfen biraz sonra tekrar deneyin."
            elif "timeout" in error_str.lower():
                user_message = "Baglanti zaman asimina ugradi. Lutfen tekrar deneyin."
            else:
                user_message = "Tarif olusturulurken beklenmeyen bir hata olustu. Lutfen tekrar deneyin."

            return {
                "success": False,
                "error": "generation_failed",
                "message": user_message,
                "detail": error_str,
                "elapsed_ms": elapsed_ms,
            }


# Singleton instance
gemini_service = GeminiService()
