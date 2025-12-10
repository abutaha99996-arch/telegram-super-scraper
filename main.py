#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import asyncio
import configparser
from datetime import datetime
from colorama import init, Fore, Style
from telethon import TelegramClient
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.tl.types import InputPeerUser, InputPeerEmpty
from telethon.errors import (
    FloodWaitError, ChannelPrivateError, UserNotParticipantError,
    UserPrivacyRestrictedError, ChatAdminRequiredError
)

# محاولة استيراد مكتبات إصلاح النص العربي
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    
    def format_arabic(text):
        """تنسيق النص العربي للعرض الصحيح"""
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
except ImportError:
    def format_arabic(text):
        """بديل إذا لم تكن المكتبات مثبتة"""
        return text

# تهيئة Colorama
init(autoreset=True)

class Colors:
    """ألوان للواجهة"""
    RED = Fore.RED
    GREEN = Fore.GREEN
    YELLOW = Fore.YELLOW
    BLUE = Fore.BLUE
    MAGENTA = Fore.MAGENTA
    CYAN = Fore.CYAN
    WHITE = Fore.WHITE
    RESET = Fore.RESET

class TelegramSuperScraper:
    def __init__(self):
        self.config_file = 'config.ini'
        self.sessions_dir = 'sessions'
        self.exports_dir = 'exports'
        self.logs_dir = 'logs'
        self.current_client = None
        self.current_session = None
        self.setup_directories()
        self.load_config()
    
    def setup_directories(self):
        """إنشاء المجلدات اللازمة"""
        for directory in [self.sessions_dir, self.exports_dir, self.logs_dir]:
            os.makedirs(directory, exist_ok=True)
    
    def load_config(self):
        """تحميل الإعدادات"""
        self.config = configparser.ConfigParser()
        if os.path.exists(self.config_file):
            self.config.read(self.config_file, encoding='utf-8')
        else:
            self.create_default_config()
    
    def create_default_config(self):
        """إنشاء إعدادات افتراضية"""
        self.config['TELEGRAM'] = {
            'api_id': '',
            'api_hash': '',
            'phone': ''
        }
        self.config['SETTINGS'] = {
            'language': 'arabic',
            'delay_between_requests': '2',
            'max_members_per_request': '200'
        }
        self.config['PROXY'] = {
            'enabled': 'false',
            'type': 'socks5',
            'host': '',
            'port': '',
            'username': '',
            'password': ''
        }
        with open(self.config_file, 'w', encoding='utf-8') as f:
            self.config.write(f)
    
    def print_header(self):
        """طباعة رأس البرنامج"""
        header = f"""
{Colors.CYAN}╔══════════════════════════════════════════════════════════╗
║{Colors.YELLOW}         Telegram Super Scraper v2.0{Colors.CYAN}                     ║
║{Colors.WHITE}           Advanced Telegram Group Manager{Colors.CYAN}                ║
║{Colors.RED}        For legal use only - Respect privacy{Colors.CYAN}               ║
╚══════════════════════════════════════════════════════════╝
{Colors.RESET}
        """
        print(header)
    
    def print_menu(self, title, options):
        """طباعة قائمة"""
        print(f"\n{Colors.CYAN}╔══════════════════════════════════════════╗")
        print(f"║{Colors.YELLOW}          {title:^36}{Colors.CYAN} ║")
        print(f"╠══════════════════════════════════════════╣")
        
        for key, value in options.items():
            if self.config['SETTINGS'].get('language', 'arabic') == 'arabic':
                display_text = format_arabic(value)
            else:
                display_text = value
            print(f"║ {Colors.GREEN}{key}.{Colors.WHITE} {display_text:<34} {Colors.CYAN}║")
        
        print(f"╚══════════════════════════════════════════╝")
    
    def get_input(self, prompt):
        """الحصول على إدخال من المستخدم"""
        if self.config['SETTINGS'].get('language', 'arabic') == 'arabic':
            prompt = format_arabic(prompt)
        return input(f"\n{Colors.YELLOW}[?]{Colors.CYAN} {prompt}: {Colors.GREEN}")
    
    def print_message(self, msg_type, message):
        """طباعة رسالة بأنواع مختلفة"""
        icons = {
            'info': f'{Colors.BLUE}[ℹ]',
            'success': f'{Colors.GREEN}[✓]',
            'warning': f'{Colors.YELLOW}[⚠]',
            'error': f'{Colors.RED}[✗]',
            'progress': f'{Colors.MAGENTA}[↻]'
        }
        
        if self.config['SETTINGS'].get('language', 'arabic') == 'arabic':
            message = format_arabic(message)
        
        print(f"{icons.get(msg_type, '[ ]')} {Colors.WHITE}{message}{Colors.RESET}")
    
    async def setup_credentials(self):
        """إعداد بيانات الدخول"""
        self.print_message('info', 'إعداد بيانات الدخول')
        
        api_id = self.get_input('أدخل API ID (من my.telegram.org)')
        api_hash = self.get_input('أدخل API Hash')
        phone = self.get_input('أدخل رقم الهاتف (مع مفتاح الدولة، مثال: +963123456789)')
        
        self.config['TELEGRAM']['api_id'] = api_id
        self.config['TELEGRAM']['api_hash'] = api_hash
        self.config['TELEGRAM']['phone'] = phone
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            self.config.write(f)
        
        self.print_message('success', 'تم حفظ بيانات الدخول')
        return True
    
    async def setup_proxy(self):
        """إعداد بروكسي"""
        self.print_message('info', 'إعداد اتصال VPN/Proxy')
        
        use_proxy = self.get_input('هل تريد استخدام بروكسي؟ (y/n)').lower()
        
        if use_proxy == 'y':
            proxy_type = self.get_input('نوع البروكسي (socks5/http)')
            proxy_host = self.get_input('عنوان البروكسي')
            proxy_port = self.get_input('منفذ البروكسي')
            username = self.get_input('اسم المستخدم (اتركه فارغاً إن لم يكن موجوداً)')
            password = self.get_input('كلمة المرور (اتركه فارغاً إن لم يكن موجوداً)')
            
            self.config['PROXY']['enabled'] = 'true'
            self.config['PROXY']['type'] = proxy_type
            self.config['PROXY']['host'] = proxy_host
            self.config['PROXY']['port'] = proxy_port
            self.config['PROXY']['username'] = username
            self.config['PROXY']['password'] = password
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                self.config.write(f)
            
            self.print_message('success', 'تم حفظ إعدادات البروكسي')
        else:
            self.config['PROXY']['enabled'] = 'false'
            with open(self.config_file, 'w', encoding='utf-8') as f:
                self.config.write(f)
            self.print_message('info', 'تم تعطيل البروكسي')
    
    def get_client(self, session_name=None):
        """إنشاء عميل تليجرام"""
        if not self.config['TELEGRAM'].get('api_id') or not self.config['TELEGRAM'].get('api_hash'):
            self.print_message('error', 'لم يتم إعداد بيانات API. الرجاء إعدادها أولاً.')
            return None
        
        try:
            api_id = int(self.config['TELEGRAM']['api_id'])
        except ValueError:
            self.print_message('error', 'API ID يجب أن يكون رقماً')
            return None
        
        api_hash = self.config['TELEGRAM']['api_hash']
        
        proxy = None
        if self.config['PROXY'].get('enabled', 'false').lower() == 'true':
            try:
                proxy = {
                    'proxy_type': self.config['PROXY']['type'],
                    'addr': self.config['PROXY']['host'],
                    'port': int(self.config['PROXY']['port']),
                    'username': self.config['PROXY'].get('username', '') or None,
                    'password': self.config['PROXY'].get('password', '') or None,
                }
            except ValueError as e:
                self.print_message('warning', f'إعدادات بروكسي غير صالحة: {e}')
                proxy = None
        
        session_path = os.path.join(self.sessions_dir, f"{session_name}.session" if session_name else "default.session")
        return TelegramClient(session_path, api_id, api_hash, proxy=proxy)
    
    async def list_sessions(self):
        """عرض الجلسات المتاحة"""
        sessions = []
        for file in os.listdir(self.sessions_dir):
            if file.endswith('.session'):
                sessions.append(file[:-8])  # إزالة .session
        return sessions
    
    async def login(self):
        """تسجيل الدخول"""
        self.print_message('info', 'تسجيل الدخول')
        
        sessions = await self.list_sessions()
        
        if sessions:
            self.print_message('info', 'الجلسات المتاحة:')
            for idx, session in enumerate(sessions, 1):
                print(f"    {Colors.GREEN}{idx}.{Colors.WHITE} {session}")
            
            choice = self.get_input('اختر رقم الجلسة أو أدخل 0 لجلسة جديدة')
            
            try:
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(sessions):
                    session_name = sessions[choice_idx]
                else:
                    session_name = self.get_input('أدخل اسم للجلسة الجديدة')
            except ValueError:
                session_name = self.get_input('أدخل اسم للجلسة الجديدة')
        else:
            session_name = self.get_input('أدخل اسم للجلسة الجديدة')
        
        client = self.get_client(session_name)
        if not client:
            return None, None
        
        try:
            await client.start(phone=self.config['TELEGRAM']['phone'])
            me = await client.get_me()
            self.print_message('success', f'تم تسجيل الدخول كـ {me.first_name} (@{me.username})')
            self.current_client = client
            self.current_session = session_name
            return client, session_name
        except Exception as e:
            self.print_message('error', f'فشل تسجيل الدخول: {str(e)}')
            return None, None
    
    async def scrape_members(self, group_link):
        """جمع أعضاء المجموعة"""
        if not self.current_client:
            self.print_message('error', 'يجب تسجيل الدخول أولاً')
            return []
        
        try:
            self.print_message('progress', 'جمع معلومات المجموعة...')
            group = await self.current_client.get_entity(group_link)
            
            self.print_message('info', f'المجموعة: {group.title}')
            
            filter_options = {
                '1': 'جميع الأعضاء',
                '2': 'الإداريين فقط',
                '3': 'الأعضاء النشطين',
                '4': 'الأعضاء مع معرفات'
            }
            self.print_menu('تصفية الأعضاء', filter_options)
            filter_choice = self.get_input('اختر نوع التصفية')
            
            members = []
            total_count = 0
            
            self.print_message('progress', 'بدأ جمع الأعضاء...')
            
            async for user in self.current_client.iter_participants(group, aggressive=True):
                total_count += 1
                
                # تطبيق الفلتر المختار
                if filter_choice == '2' and not user.participant.admin:
                    continue
                elif filter_choice == '3' and not (user.status or getattr(user, 'online', False)):
                    continue
                elif filter_choice == '4' and not user.username:
                    continue
                
                member_data = {
                    'id': user.id,
                    'access_hash': user.access_hash,
                    'first_name': user.first_name or '',
                    'last_name': user.last_name or '',
                    'username': user.username or '',
                    'phone': user.phone or '',
                    'is_bot': user.bot,
                    'is_admin': getattr(user.participant, 'admin', False) if hasattr(user, 'participant') else False,
                    'scraped_at': datetime.now().isoformat()
                }
                members.append(member_data)
                
                if len(members) % 50 == 0:
                    self.print_message('progress', f'تم جمع {len(members)} من {total_count} عضو')
            
            # حفظ البيانات
            if members:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{self.exports_dir}/members_{group.id}_{timestamp}.json"
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(members, f, ensure_ascii=False, indent=2)
                
                self.print_message('success', f'تم حفظ {len(members)} عضو في {filename}')
                return members
            else:
                self.print_message('warning', 'لم يتم العثور على أعضاء مطابقين للمعايير')
                return []
                
        except Exception as e:
            self.print_message('error', f'خطأ في جمع الأعضاء: {str(e)}')
            return []
    
    async def transfer_members(self, source_group, target_group, members_file=None):
        """نقل الأعضاء بين المجموعات"""
        if not self.current_client:
            self.print_message('error', 'يجب تسجيل الدخول أولاً')
            return
        
        try:
            self.print_message('progress', 'جمع معلومات المجموعات...')
            source = await self.current_client.get_entity(source_group)
            target = await self.current_client.get_entity(target_group)
            
            self.print_message('info', f'المصدر: {source.title}')
            self.print_message('info', f'الهدف: {target.title}')
            
            # تحميل الأعضاء
            if members_file and os.path.exists(members_file):
                with open(members_file, 'r', encoding='utf-8') as f:
                    members = json.load(f)
                self.print_message('info', f'تم تحميل {len(members)} عضو من الملف')
            else:
                members = await self.scrape_members(source_group)
            
            if not members:
                self.print_message('warning', 'لا يوجد أعضاء لنقلهم')
                return
            
            # تأكيد النقل
            confirm = self.get_input(f'هل تريد نقل {len(members)} عضو؟ (y/n)').lower()
            if confirm != 'y':
                self.print_message('info', 'تم إلغاء النقل')
                return
            
            # بدء النقل
            transferred = 0
            failed = []
            delay = int(self.config['SETTINGS'].get('delay_between_requests', '2'))
            
            for idx, member in enumerate(members, 1):
                try:
                    # إنشاء كائن المستخدم
                    user = InputPeerUser(member['id'], member['access_hash'])
                    
                    # دعوة المستخدم
                    await self.current_client(InviteToChannelRequest(target, [user]))
                    
                    transferred += 1
                    name = f"{member['first_name']} {member['last_name']}".strip() or f"User_{member['id']}"
                    self.print_message('success', f'[{idx}/{len(members)}] تم نقل: {name}')
                    
                    # تأخير بين الطلبات
                    if idx < len(members):
                        await asyncio.sleep(delay)
                        
                except FloodWaitError as e:
                    wait_time = e.seconds
                    self.print_message('warning', f'تم تقييد الحساب، الانتظار {wait_time} ثانية...')
                    await asyncio.sleep(wait_time)
                    continue
                except (UserPrivacyRestrictedError, UserNotParticipantError, ChannelPrivateError) as e:
                    failed.append({'member': member, 'error': str(e)})
                    self.print_message('warning', f'فشل نقل عضو: {str(e)}')
                except Exception as e:
                    failed.append({'member': member, 'error': str(e)})
                    self.print_message('error', f'خطأ غير متوقع: {str(e)}')
            
            # حفظ التقرير
            report = {
                'source_group': source_group,
                'target_group': target_group,
                'total_members': len(members),
                'transferred': transferred,
                'failed': len(failed),
                'failed_details': failed,
                'transfer_date': datetime.now().isoformat()
            }
            
            report_file = f"{self.logs_dir}/transfer_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            self.print_message('success', f'اكتمل النقل!')
            self.print_message('info', f'• تم نقل: {transferred} عضو')
            self.print_message('info', f'• فشل: {len(failed)} عضو')
            self.print_message('info', f'• التقرير: {report_file}')
            
        except Exception as e:
            self.print_message('error', f'خطأ في النقل: {str(e)}')
    
    async def export_messages(self, group_link, limit=1000):
        """تصدير رسائل المجموعة"""
        if not self.current_client:
            self.print_message('error', 'يجب تسجيل الدخول أولاً')
            return
        
        try:
            self.print_message('progress', 'جمع معلومات المجموعة...')
            group = await self.current_client.get_entity(group_link)
            
            self.print_message('info', f'المجموعة: {group.title}')
            
            messages = []
            self.print_message('progress', 'جمع الرسائل...')
            
            async for message in self.current_client.iter_messages(group, limit=limit):
                msg_data = {
                    'id': message.id,
                    'date': message.date.isoformat() if message.date else None,
                    'sender_id': message.sender_id,
                    'text': message.text or '',
                    'has_media': bool(message.media),
                    'group_id': group.id,
                    'group_name': group.title
                }
                messages.append(msg_data)
                
                if len(messages) % 100 == 0:
                    self.print_message('progress', f'تم جمع {len(messages)} رسالة')
            
            # حفظ الرسائل
            if messages:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                # JSON
                json_file = f"{self.exports_dir}/messages_{group.id}_{timestamp}.json"
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(messages, f, ensure_ascii=False, indent=2)
                
                # TXT
                txt_file = f"{self.exports_dir}/messages_{group.id}_{timestamp}.txt"
                with open(txt_file, 'w', encoding='utf-8') as f:
                    f.write(f"رسائل مجموعة: {group.title}\n")
                    f.write(f"عدد الرسائل: {len(messages)}\n")
                    f.write("="*50 + "\n\n")
                    
                    for msg in messages:
                        f.write(f"[{msg['date']}] User_{msg['sender_id']}:\n")
                        f.write(f"{msg['text'][:200]}\n")
                        f.write("-"*40 + "\n")
                
                self.print_message('success', f'تم حفظ {len(messages)} رسالة')
                self.print_message('info', f'• ملف JSON: {json_file}')
                self.print_message('info', f'• ملف نصي: {txt_file}')
            else:
                self.print_message('warning', 'لم يتم العثور على رسائل')
                
        except Exception as e:
            self.print_message('error', f'خطأ في جمع الرسائل: {str(e)}')
    
    async def main_menu(self):
        """القائمة الرئيسية"""
        while True:
            os.system('cls' if os.name == 'nt' else 'clear')
            self.print_header()
            
            menu_options = {
                '1': 'تسجيل الدخول',
                '2': 'إعدادات API',
                '3': 'إعدادات البروكسي',
                '4': 'جمع أعضاء المجموعة',
                '5': 'نقل الأعضاء بين المجموعات',
                '6': 'تصدير رسائل المجموعة',
                '7': 'النقل السريع',
                '8': 'الخروج'
            }
            
            self.print_menu('القائمة الرئيسية', menu_options)
            choice = self.get_input('اختر خياراً')
            
            if choice == '1':
                await self.login()
                input("\nاضغط Enter للمتابعة...")
            
            elif choice == '2':
                await self.setup_credentials()
                input("\nاضغط Enter للمتابعة...")
            
            elif choice == '3':
                await self.setup_proxy()
                input("\nاضغط Enter للمتابعة...")
            
            elif choice == '4':
                if self.current_client:
                    group_link = self.get_input('أدخل رابط المجموعة')
                    limit = self.get_input('الحد الأقصى للأعضاء (اتركه فارغاً للجميع)')
                    limit = int(limit) if limit.strip() else 0
                    await self.scrape_members(group_link)
                else:
                    self.print_message('error', 'يجب تسجيل الدخول أولاً')
                input("\nاضغط Enter للمتابعة...")
            
            elif choice == '5':
                if self.current_client:
                    source = self.get_input('رابط المجموعة المصدر')
                    target = self.get_input('رابط المجموعة الهدف')
                    members_file = self.get_input('مسار ملف الأعضاء (اختياري، اتركه فارغاً لجمع جديد)')
                    members_file = members_file if members_file.strip() else None
                    await self.transfer_members(source, target, members_file)
                else:
                    self.print_message('error', 'يجب تسجيل الدخول أولاً')
                input("\nاضغط Enter للمتابعة...")
            
            elif choice == '6':
                if self.current_client:
                    group_link = self.get_input('أدخل رابط المجموعة')
                    limit = self.get_input('عدد الرسائل (افتراضي 1000)')
                    limit = int(limit) if limit.strip() else 1000
                    await self.export_messages(group_link, limit)
                else:
                    self.print_message('error', 'يجب تسجيل الدخول أولاً')
                input("\nاضغط Enter للمتابعة...")
            
            elif choice == '7':
                if self.current_client:
                    self.print_message('info', 'النقل السريع - نقل جميع الأعضاء من مجموعة إلى أخرى')
                    source = self.get_input('رابط المجموعة المصدر')
                    target = self.get_input('رابط المجموعة الهدف')
                    confirm = self.get_input('هل تريد المتابعة؟ (y/n)').lower()
                    if confirm == 'y':
                        await self.transfer_members(source, target)
                else:
                    self.print_message('error', 'يجب تسجيل الدخول أولاً')
                input("\nاضغط Enter للمتابعة...")
            
            elif choice == '8':
                self.print_message('info', 'مع السلامة!')
                if self.current_client:
                    await self.current_client.disconnect()
                break
            
            else:
                self.print_message('error', 'اختيار غير صحيح')
                input("\nاضغط Enter للمتابعة...")

async def main():
    scraper = TelegramSuperScraper()
    await scraper.main_menu()

if __name__ == "__main__":
    # إعدادات خاصة بـ Windows
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.RED}[!] تم إيقاف البرنامج{Colors.RESET}")
    except Exception as e:
        print(f"\n{Colors.RED}[!] خطأ غير متوقع: {e}{Colors.RESET}")
