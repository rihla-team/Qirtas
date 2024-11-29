from .base_tool import TerminalTool
import pint
from forex_python.bitcoin import BtcConverter
from forex_python.converter import CurrencyRates, RatesNotAvailableError
import requests.exceptions
import json
import os
import time


class UnitConverter(TerminalTool):
    def __init__(self, terminal):
        super().__init__(terminal)
        # استخدام التحميل الكسول للموارد
        self._ureg = None
        self._btc = None
        self._currency_rates = None
        self._units_data = None
        
        # تخزين مؤقت للتحويلات الشائعة
        self._conversion_cache = {}
        self._currency_cache = {}
        self._cache_timeout = 300  # 5 دقائق
        
        # تعريف الأوامر المدعومة مع تحديث الاختصارات
        self.commands = {
            'وحدات': {'func': self.convert_units, 'aliases': ['-و', 'و', '--وحدات']},
            'عملات': {'func': self.convert_currency, 'aliases': ['-ع', 'ع', '--عملات']},
            'بتكوين': {'func': self.convert_bitcoin, 'aliases': ['-ب', 'ب', '--بتكوين']},
            'معلومات': {'func': self.show_unit_info, 'aliases': ['-م', '--معلومات']},
            'فئات': {'func': self.show_categories, 'aliases': ['-ف', '--فئات']},
            'مساعدة': {'func': self.show_help, 'aliases': ['-ا', '--مساعدة', '--اوامر']}
        }

        self.stats = {
            'conversions': 0,
            'errors': 0,
            'most_used_units': {},
            'last_conversions': []
        }

    @property
    def ureg(self):
        """تحميل كسول لمكتبة pint"""
        if self._ureg is None:
            self._ureg = pint.UnitRegistry(autoconvert_offset_to_baseunit=True)
            # لا نحتاج لتعريف الوحدات هنا لأنها موجودة في ملف البيانات
        return self._ureg

    @property
    def units_data(self):
        """تحميل كسول لبيانات الوحدات"""
        if self._units_data is None:
            self._load_units_data()
        return self._units_data

    def _load_units_data(self):
        """تحميل بيانات الوحدات من الملف"""
        try:
            current_dir = os.path.dirname(os.path.dirname(__file__))
            json_path = os.path.join(current_dir, 'resources', 'units_data.json')
            with open(json_path, 'r', encoding='utf-8') as f:
                self._units_data = json.load(f)['units']
        except Exception as e:
            self.terminal.append_text(
                f"خطأ في تحميل بيانات الوحدات: {str(e)}\n",
                self.terminal.colors['error']
            )
            self._units_data = {}

    def process_command(self, command, args):
        """معالجة الأوامر"""
        # تحويل الاختصارات إلى الأوامر الكاملة
        for cmd, data in self.commands.items():
            if command in data['aliases']:
                command = cmd
                break
            
        # تنفيذ الأمر المناسب
        if command in self.commands:
            self.commands[command]['func'](args)
        else:
            self.terminal.append_text(
                f"الأمر '{command}' غير معروف.\n"
                "استخدم 'مساعدة' لعرض قائمة الأوامر المتاحة.\n",
                self.terminal.colors['error']
            )

    def convert_currency(self, args):
        """تحويل العملات"""
        if len(args) != 4 or args[2] != 'الى':
            self.terminal.append_text(
                "الصيغة: عملات <المبلغ> <العملة الأصلية> الى <العملة المطلوبة>\n"
                "مثال: عملات 100 دولار الى يور\n", 
                self.terminal.colors['error']
            )
            return

        try:
            amount = float(args[0])
            from_currency = self._get_currency_code(args[1])
            to_currency = self._get_currency_code(args[3])

            if not from_currency or not to_currency:
                self.terminal.append_text(
                    "خطأ: العملة غير معروفة. الرجاء استخدام العملات المدعومة.\n",
                    self.terminal.colors['error']
                )
                return

            try:
                # محاولة الحصول على سعر الصرف
                rate = self.c.get_rate(from_currency, to_currency)
                result = amount * rate

                # تنسيق أسماء العملات بالعربي
                currency_names = {
                    'USD': 'دولار أمريكي',
                    'EUR': 'يورو',
                    'GBP': 'جنيه إسترليني',
                    'JPY': 'ين ياباني',
                    'SAR': 'ريال سعودي',
                    'AED': 'درهم إماراتي',
                    'KWD': 'دينار كويتي',
                    'EGP': 'جنيه مصري',
                    'CNY': 'يوان صيني',
                    'RUB': 'روبل روسي',
                    'TRY': 'ليرة تركية',
                    'ILS': 'شيكل إسرائيلي',
                    'CHF': 'فرنك سويسري',
                    'INR': 'روبية هندية'
                }

                from_currency_name = currency_names.get(from_currency, from_currency)
                to_currency_name = currency_names.get(to_currency, to_currency)

                self.terminal.append_text("\n")
                self.terminal.append_text(
                    f"تحويل من {from_currency_name} إلى {to_currency_name}:\n",
                    self.terminal.colors['header']
                )
                self.terminal.append_text(
                    f"  {amount:,.2f} {from_currency_name} = {result:,.2f} {to_currency_name}\n",
                    self.terminal.colors['success']
                )
                self.terminal.append_text(
                    f"  سعر الصرف: 1 {from_currency_name} = {rate:,.4f} {to_currency_name}\n"
                )
                self.terminal.append_text("\n")

            except (RatesNotAvailableError, requests.exceptions.RequestException) as e:
                self.terminal.append_text(
                    "خطأ: لا يمكن الوصول إلى خدمة تحويل العملات.\n"
                    "تأكد من اتصالك بالإنترنت وحاول مرة أخرى.\n",
                    self.terminal.colors['error']
                )
            except ValueError as e:
                self.terminal.append_text(
                    f"خطأ: العملة غير مدعومة أو غير صالحة.\n"
                    f"الرجاء استخدام العملات المدعومة فقط.\n",
                    self.terminal.colors['error']
                )

        except Exception as e:
            self.terminal.append_text(
                "خطأ في تحويل العملة.\n"
                "تأكد من صحة المدخلات وحاول مرة أخرى.\n"
                f"تفاصيل الخطأ: {str(e)}\n",
                self.terminal.colors['error']
            )

    def _get_currency_code(self, arabic_name):
        """تحويل اسم العملة من العربية إلى الرمز الإنجليزي"""
        # إذا كان الإدخال بالفعل رمز عملة إنجليزي
        if arabic_name.upper() in ['USD', 'EUR', 'GBP', 'EGP', 'SAR', 'AED', 'KWD', 'JPY', 'CNY', 'RUB', 'TRY', 'ILS', 'CHF', 'INR']:
            return arabic_name.upper()
        
        # البحث في قاموس العملات
        return self.currency_map.get(arabic_name)

    def convert_bitcoin(self, args):
        """تحويل البتكوين"""
        if len(args) != 3 or args[1] != 'الى':
            self.terminal.append_text(
                "الصيغة: بتكوين <المبلغ> الى <الملة>\n"
                "مثال: بتكوين 1 الى دولار\n",
                self.terminal.colors['error']
            )
            return

        try:
            amount = float(args[0])
            to_currency = self._get_currency_code(args[2])

            if not to_currency:
                self.terminal.append_text(
                    "خطأ: العملة غير معروفة. الرجاء استخدام العملات المدعومة.\n",
                    self.terminal.colors['error']
                )
                return

            # استخدام forex_python للحصول على سعر البتكوين
            c = CurrencyRates()
            btc_usd = self.btc.get_latest_price('USD')  # الحصول على سعر البتكوين بالدولار
            
            if to_currency != 'USD':
                # تحويل من الدولار إلى العملة المطلوبة
                usd_rate = c.get_rate('USD', to_currency)
                rate = btc_usd * usd_rate
            else:
                rate = btc_usd

            result = amount * rate

            # تنسيق اسم العملة بالعربي
            currency_names = {
                'USD': 'دولار',
                'EUR': 'يورو',
                'GBP': 'جنيه إسترليني',
                'JPY': 'ين ياباني',
                'SAR': 'ريال سعودي',
                'AED': 'درهم إماراتي',
                'KWD': 'دينار كويتي',
                'EGP': 'جنيه مصري'
            }

            currency_name = currency_names.get(to_currency, to_currency)

            self.terminal.append_text("\n")
            self.terminal.append_text(
                f"تحويل البتكوين إلى {currency_name}:\n",
                self.terminal.colors['header']
            )
            self.terminal.append_text(
                f"  {amount:,.8f} بتكوين = {result:,.2f} {currency_name}\n",
                self.terminal.colors['success']
            )
            self.terminal.append_text("\n")

        except Exception as e:
            self.terminal.append_text(
                f"خطأ في تحويل البتكوين: {str(e)}\n"
                "تأكد من اتصالك بالإنترنت وصح العملة المدخلة\n",
                self.terminal.colors['error']
            )

    def show_help(self, args=None):
        """عرض المساعدة وطريقة الاستعمال"""
        help_text = """
🔄 محول الوحدات والعملات

الأوامر المتاحة:
──────────────────────

1️⃣ تحويل الوحدات:
   الأمر: وحدات، -و، --وحدات
   الصيغة: وحدات <القيمة> <الوحدة الأصلية> الى <الوحدة المطلوبة>
   أمثلة:
   - وحدات 100 ذراع الى فرسخ
   - وحدات 50 رطل الى قنطار
   - وحدات 30 درجة_مئوية الى درجة_فهرنهايت

2️⃣ تحويل العملات:
   الأمر: عملات، -ع، --عملات
   الصيغة: عملات <المبلغ> <العملة الأصلية> الى <الملة المطلوبة>
   أمثلة:
   - عملات 100 دولار الى ريال
   - عملات 500 ريال الى دينار
   - عملات 1000 درهم الى جنيه

3️⃣ تحويل البتكوين:
   الأمر: بتكوين، -ب، --بتكوين
   الصيغة: بتكوين <المبلغ> الى <العملة>
   أمثلة:
   - بتكوين 1 الى جنيه
   - بتكوين 0.5 الى درهم

4️⃣ عرض معلومات عن وحدة:
   الأمر: معلومات ، --معلومات
   الصيغة: معلومات <اسم الوحدة>
   أمثلة:
   - تحويل معلومات متر
   - تحويل معلومات رطل
   - تحويل معلمات واط

5️⃣ عرض فئات الوحدات:
   الأمر: فئات، -ف، --فئات
   يعرض جميع فئات الوحدات المتوفرة ووحداتها
   مثال: تحويل فئات
   تحويل فئات الطول

نصائح مهمة:
──────────────────────
• استخدم الأمر 'فئات' للاطلاع على جميع الوحدات المتاحة
• استخدم الأمر 'معلومات' للحصول على تفاصيل عن وحدة معينة
• تأكد من كتابة 'الى' باللغة العربية في جميع عمليات التحويل
• يمكنك استخدام الاختصارات (-و، -ع، -ب، -م، -ف) للأوامر

أمثلة إضافية:
──────────────────────
▸ تحويل وحدات القياس:
  تحويل وحدات 100 قصبة الى جريب
  تحويل وحدات 75 فرسخ_بالساعة الى ميل_بالساعة
  تحويل وحدات 2 قنطار الى رطل

▸ تحويل العملات:
  تحويل عملات 1000 دولار الى يورو
  تحويل عملات 5000 ريال الى دينار_كويتي
  تحويل عملات 100 جنيه الى درهم

▸ معلومات الوحدات:
  تحويل معلومات فرسخ
  تحويل معلومات صاع 
  تحويل معلومات فدان 

للمساعدة:
──────────────────────
• استخدم --مساعدة لعرض هذه القائمة
• استخدم --اوامر لعرض قائمة الأوامر المتاحة
"""
        self.terminal.append_text(help_text, self.terminal.colors['output'])

    def convert_units(self, args):
        """تحويل الوحدات"""
        try:
            # التحقق من صحة عدد المعاملات
            if len(args) != 4:
                self.terminal.append_text(
                    "الصيغة: وحدات <القيمة> <الوحدة الأصلية> الى <الوحدة المطلوبة>\n"
                    "مثال: وحدات 100 ذراع الى فرسخ\n",
                    self.terminal.colors['error']
                )
                return
            
            # التحقق من كلمة "الى"
            if args[2].strip() != 'الى':
                self.terminal.append_text(
                    "يجب استخدام كلمة 'الى' بين الوحدتين\n"
                    "مثال: وحدات 100 ذراع الى فرسخ\n",
                    self.terminal.colors['error']
                )
                return

            value = float(args[0])
            from_unit = args[1]
            to_unit = args[3]

            # البحث عن بيانات الوحدات وإجراء التحويل
            from_unit_data = self._find_unit_data(from_unit)
            to_unit_data = self._find_unit_data(to_unit)

            if not from_unit_data or not to_unit_data:
                if not from_unit_data:
                    self.handle_error('unknown_unit', from_unit)
                if not to_unit_data:
                    self.handle_error('unknown_unit', to_unit)
                return

            result = self._perform_conversion(value, from_unit_data, to_unit_data)
            if result is not None:
                self._display_conversion_result(value, result, from_unit_data, to_unit_data)

        except ValueError as e:
            self.terminal.append_text(
                f"خطأ: {str(e)}\n",
                self.terminal.colors['error']
            )

    def _find_unit_data(self, unit_name):
        """البحث عن بيانات الوحدة"""
        # تنظيف اسم الوحدة
        unit_name = unit_name.strip().lower()
        
        # البحث في البيانات
        for key, unit_data in self.units_data.items():
            # التحقق من المفتاح نفسه
            if key.lower() == unit_name:
                return unit_data
            
            # التحقق من الاسم العربي
            if unit_data.get('arabic', '').lower() == unit_name:
                return unit_data
            
            # التحقق من الاسم الإنجليزي
            if unit_data.get('english', '').lower() == unit_name:
                return unit_data
            
            # التحقق من الأسماء البديلة
            if unit_name in [alias.lower() for alias in unit_data.get('aliases', [])]:
                return unit_data
            
            # معالجة خاصة لدرجات الحرارة
            if unit_name in ['درجة مئوية', 'مئوية', 'درجة_مئوية'] and key == 'درجة_مئوية':
                return unit_data
            if unit_name in ['درجة فهرنهايت', 'فهرنهايت', 'درجة_فهرنهايت'] and key == 'درجة_فهرنهايت':
                return unit_data
            
        return None

    def _format_scientific_notation(self, number):
        """تنسيق الرقم بالصيغة العلمية"""
        # تحويل الرقم إلى الصيغة العلمية
        sci_notation = f"{number:.2e}"
        # تقسيم الرقم إلى جزأين: الرقم والأس
        base, exponent = sci_notation.split('e')
        # تحويل الأس إلى رقم
        exp_num = int(exponent)
        # تنسيق النتيجة
        return f"{float(base):.2f} × 10^{exp_num}"

    def _display_conversion_result(self, value, result, from_unit_data, to_unit_data):
        """عرض نتيجة التحويل مع التفاصيل"""
        if result is None:
            return
        
        self.terminal.append_text("\n")
        self.terminal.append_text(
            f"التحويل من {from_unit_data['arabic']} إلى {to_unit_data['arabic']}:\n",
            self.terminal.colors['header']
        )
        
        # تنسيق النتيجة
        if abs(result) < 0.0001 or abs(result) >= 1000000:
            formatted_result = self._format_scientific_notation(result)
        else:
            decimal_places = 4 if abs(result) < 0.1 else 2
            formatted_result = f"{result:.{decimal_places}f}"
        
        # تنسيق معامل التحويل
        conversion_rate = result / value
        if abs(conversion_rate) < 0.0001 or abs(conversion_rate) >= 1000000:
            formatted_rate = self._format_scientific_notation(conversion_rate)
        else:
            decimal_places = 4 if abs(conversion_rate) < 0.1 else 2
            formatted_rate = f"{conversion_rate:.{decimal_places}f}"
        
        # عرض النتيجة ومعامل التحويل
        self.terminal.append_text(
            f"  {value:.2f} {from_unit_data['arabic']} = {formatted_result} {to_unit_data['arabic']}\n",
            self.terminal.colors['success']
        )
        self.terminal.append_text(
            f"  \n (1 {from_unit_data['arabic']} = {formatted_rate} {to_unit_data['arabic']})\n",
            self.terminal.colors['info']
        )
        
        # عرض الوصف والأمثلة إذا كانت متوفرة
        if 'description' in to_unit_data:
            self.terminal.append_text(
                f"\nمعلومات عن {to_unit_data['arabic']}:\n{to_unit_data['description']}\n",
                self.terminal.colors['info']
            )
        if 'examples' in to_unit_data:
            self.terminal.append_text(
                f"\nأمثلة:\n{to_unit_data['examples']}\n",
                self.terminal.colors['info']
            )
        self.terminal.append_text("\n")

    def _perform_conversion(self, value, from_unit_data, to_unit_data):
        """إجراء التحويل مع معالجة خاصة لدرجات الحرارة"""
        try:
            from_unit = from_unit_data['english'].lower()
            to_unit = to_unit_data['english'].lower()
            
            # استخدام الوحدات مباشرة من البيان��ت
            quantity = self.ureg.Quantity(float(value), from_unit)
            result = quantity.to(to_unit).magnitude
            return result
            
        except Exception as e:
            self.terminal.append_text(
                f"خطأ في التحويل: {str(e)}\n"
                "تأكد من توافق الوحدات المستخدمة\n",
                self.terminal.colors['error']
            )
            return None

    def _convert_temperature(self, value, from_unit, to_unit):
        """تحويل درجات الحرارة باستخدام المعادلات المباشرة"""
        try:
            # تنظيف أسماء الوحدات
            from_unit = from_unit.lower()
            to_unit = to_unit.lower()
            
            # التحويلات المباشرة
            if from_unit == 'celsius' and to_unit == 'fahrenheit':
                return (value * 9/5) + 32
            elif from_unit == 'fahrenheit' and to_unit == 'celsius':
                return (value - 32) * 5/9
            elif from_unit == 'celsius' and to_unit == 'kelvin':
                return value + 273.15
            elif from_unit == 'kelvin' and to_unit == 'celsius':
                return value - 273.15
            elif from_unit == 'fahrenheit' and to_unit == 'kelvin':
                celsius = (value - 32) * 5/9
                return celsius + 273.15
            elif from_unit == 'kelvin' and to_unit == 'fahrenheit':
                celsius = value - 273.15
                return (celsius * 9/5) + 32
            elif from_unit == to_unit:
                return value
            else:
                raise ValueError(f"لا يمكن التحويل من {from_unit} إلى {to_unit}")
            
        except Exception as e:
            raise ValueError(f"خطأ في تحويل درجات الحرارة: {str(e)}")

    def show_unit_info(self, args):
        """عرض معلومات تفصيلية عن وحدة معينة"""
        if not args:
            self.terminal.append_text(
                "\nخطأ: يجب تحديد اسم الوحدة\n"
                "الصيغة: معلومات <اسم الوحدة>\n",
                self.terminal.colors['error']
            )
            return

        unit_key = args[0]
        unit_data = self._find_unit_data(unit_key)
        
        if not unit_data:
            self.terminal.append_text(
                f"خطأ: الوحدة '{unit_key}' غير موجودة\n",
                self.terminal.colors['error']
            )
            return

        self.terminal.append_text("\n")
        self.terminal.append_text(f"معلومات عن {unit_data['arabic']}:\n", self.terminal.colors['header'])
        self.terminal.append_text(f"الاسم بالإنليزية: {unit_data['english']}\n")
        
        if 'description' in unit_data:
            self.terminal.append_text(f"الوصف: {unit_data['description']}\n")
        
        if 'category' in unit_data:
            self.terminal.append_text(f"الفئة: {unit_data['category']}\n")
        
        if 'examples' in unit_data:
            self.terminal.append_text("\nأملة:\n", self.terminal.colors['info'])
            self.terminal.append_text(f"{unit_data['examples']}\n")
        
        if 'Detailed_details' in unit_data:
            self.terminal.append_text("\nتفاصيل إضافية:\n", self.terminal.colors['info'])
            self.terminal.append_text(f"{unit_data['Detailed_details']}\n")
        
        self.terminal.append_text("\n")

    def show_categories(self, args):
        """عرض فئات الوحدات المتوفرة"""
        categories = {}
        
        # تجميع الوحدات حسب الفئات
        for unit_key, unit_data in self.units_data.items():
            if 'category' in unit_data:
                category = unit_data['category']
                if category not in categories:
                    categories[category] = []
                categories[category].append(unit_data['arabic'])

        # إذا تم تحديد فئة معينة
        if args and len(args) > 0:
            category_name = ' '.join(args).strip()
            found = False
            
            # البحث عن الفئة المطلوبة
            for category, units in categories.items():
                if category.lower() == category_name.lower():
                    self.terminal.append_text(f"\nوحدات فئة {category}:\n", self.terminal.colors['header'])
                    for unit in sorted(units):
                        self.terminal.append_text(f"  - {unit}\n")
                    found = True
                    break
            
            if not found:
                # إذا لم يتم العثور على الفئة، نقترح الفئات المتاحة
                self.terminal.append_text(
                    f"\nالفئة '{category_name}' غير موجودة.\n",
                    self.terminal.colors['error']
                )
                self.terminal.append_text("\nالفئات المتاحة:\n", self.terminal.colors['info'])
                for category in sorted(categories.keys()):
                    self.terminal.append_text(f"  - {category}\n")
        else:
            # عرض جميع الفئات إذا لم يتم تحديد فئة
            self.terminal.append_text("\nفئات الوحدات المتوفرة:\n", self.terminal.colors['header'])
            
            for category, units in sorted(categories.items()):
                self.terminal.append_text(f"\n{category}:\n", self.terminal.colors['info'])
                for unit in sorted(units):
                    self.terminal.append_text(f"  - {unit}\n")
        
        self.terminal.append_text("\nللحصول على معلومات تفصيلية عن وحدة معينة، استخدم الأمر: معلومات <اسم الوحدة>\n")
        self.terminal.append_text("مثال: تحويل معلومات متر\n")
        self.terminal.append_text("\n")

    def suggest_units(self, partial_input):
        """اقتراح الوحدات المشابهة"""
        suggestions = []
        partial_input = partial_input.lower()
        
        for unit_key, unit_data in self.units_data.items():
            if 'arabic' in unit_data:
                if partial_input in unit_data['arabic'].lower():
                    suggestions.append(unit_data['arabic'])
                elif partial_input in unit_key.lower():
                    suggestions.append(unit_key)
        
        return suggestions[:5]  # إرجاع أفضل 5 اقتراحات

    def handle_error(self, error_type, details):
        """معالجة الأخطاء مع اقتراحات"""
        if error_type == 'unknown_unit':
            suggestions = self.suggest_units(details)
            self.terminal.append_text(
                f"الوحدة '{details}' غير معروفة.\n",
                self.terminal.colors['error']
            )
            if suggestions:
                self.terminal.append_text(
                    "هل تقصد أحد هذه الوحدات؟\n",
                    self.terminal.colors['info']
                )
                for suggestion in suggestions:
                    self.terminal.append_text(f"- {suggestion}\n")

    def log_conversion(self, from_unit, to_unit, success=True):
        """تسجيل إحصائيات التحويل"""
        self.stats['conversions'] += 1
        if not success:
            self.stats['errors'] += 1

        # تحديث الوحدات الأكثر استخداماً
        for unit in [from_unit, to_unit]:
            self.stats['most_used_units'][unit] = \
                self.stats['most_used_units'].get(unit, 0) + 1

        # تسجيل آخر التحويلات
        self.stats['last_conversions'].append({
            'from': from_unit,
            'to': to_unit,
            'timestamp': time.time(),
            'success': success
        })
        # الاحتفاظ بآخر 10 تحويلات فقط
        self.stats['last_conversions'] = self.stats['last_conversions'][-10:]

    def show_stats(self):
        """عرض إحصائيات الاستخدام"""
        self.terminal.append_text("\nإحصائيات الاستخدام:\n", self.terminal.colors['header'])
        self.terminal.append_text(f"عدد التحويلات: {self.stats['conversions']}\n")
        self.terminal.append_text(f"عدد الأخطاء: {self.stats['errors']}\n")
        
        # عرض الوحدات الأكثر استخداماً
        self.terminal.append_text("\nالوحدات الأكثر استخداماً:\n", self.terminal.colors['info'])
        sorted_units = sorted(
            self.stats['most_used_units'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        for unit, count in sorted_units:
            self.terminal.append_text(f"- {unit}: {count} مرة\n")

    def execute(self, args):
        """تنفيذ الأمر مع المعاملات"""
        if not args:
            self.show_help()
            return
        
        command = args[0].lower()
        
        # تحويل الاختصارات إلى الأوامر الكاملة
        for cmd, data in self.commands.items():
            if command in data['aliases']:
                command = cmd
                break
            
        # تنفيذ الأمر المناسب
        if command in self.commands:
            self.commands[command]['func'](args[1:])
        else:
            self.terminal.append_text(
                f"الأمر '{command}' غير معروف.\n"
                "استخدم 'مساعدة' لعرض قائمة الأوامر المتاحة.\n",
                self.terminal.colors['error']
            )
