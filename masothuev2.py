import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
from bs4 import BeautifulSoup
import time
import random
import cloudscraper
import unidecode

class MaSoThueApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Tra cứu Mã số thuế")
        self.root.geometry("1200x600")  # Tăng chiều rộng để chứa các cột mới

        # Constants
        self.base_url = "https://esgoo.net/api-mst"
        self.url_1900 = "https://1900.com.vn/ma-so-thue"
        self.url_congty = "https://congtydoanhnghiep.com"
        
        # Headers
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }

        # User agents
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; WOW64) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15"
        ]
        
        # Tạo giao diện
        self.create_widgets()

    def format_company_name(self, name):
        """Chuyển đổi tên công ty thành dạng không dấu và nối bằng dấu -"""
        no_accent = unidecode.unidecode(name)
        lowercase = no_accent.lower()
        formatted = '-'.join(lowercase.split())
        return formatted

    def get_company_name(self, tax_code):
        """Lấy tên công ty từ API esgoo.net"""
        try:
            url = f"{self.base_url}/{tax_code}.htm"
            headers = {
                "User-Agent": random.choice(self.user_agents),
                "Accept": "application/json"
            }
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            if result.get("error") == 0 and result.get("data"):
                name = result["data"].get("ten", "")
                if name:
                    return self.format_company_name(name)
            return None
        except Exception as e:
            print(f"Lỗi khi lấy tên công ty: {str(e)}")
            return None

    def get_company_info(self, tax_code, formatted_name, max_retries=3):
        """Lấy thông tin công ty từ masothue.com trước, sau đó từ congtydoanhnghiep.com nếu cần"""
        company_info = {
            "Mã số thuế": tax_code,
            "Tên công ty": "",
            "Tên Tiếng Anh": "",
            "Địa chỉ": "",
            "Người đại diện": "",
            "Chủ sở hữu": "",
            "Tình trạng hoạt động": "",
            "Nơi đăng ký quản lý": "",
            "Ngày cấp giấy phép": "",
            "Ngày hoạt động": "",
            "Ngành nghề chính": "",
            "Ngành nghề kinh doanh": "",
            "Lưu ý": "",
            "Tình trạng": "",
            "Quản lý bởi": "",
            "Điện thoại": ""
        }

        try:
            # Tạo scraper để bypass protection
            scraper = cloudscraper.create_scraper(
                browser={
                    'browser': 'chrome',
                    'platform': 'windows',
                    'mobile': False
                }
            )

            # Bước 1: Ưu tiên lấy thông tin từ masothue.com
            url_masothue = f"https://masothue.com/{tax_code}-{formatted_name}"
            print(f"Đang truy cập URL masothue.com: {url_masothue}")
            response = scraper.get(url_masothue, headers=self.headers)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                # Trích xuất thông tin từ masothue.com
                table = soup.find('table', class_='table-taxinfo')
                if table:
                    rows = table.find_all('tr')
                    for row in rows:
                        th = row.find('th')
                        td = row.find('td')
                        if th and td:
                            header = th.text.strip()
                            value = td.text.strip()
                            
                            if "Tên chính thức" in header:
                                company_info["Tên công ty"] = value
                            elif "Tên quốc tế" in header:
                                company_info["Tên Tiếng Anh"] = value
                            elif "Địa chỉ" in header:
                                company_info["Địa chỉ"] = value
                            elif "Người đại diện" in header:
                                company_info["Người đại diện"] = value
                            elif "Chủ sở hữu" in header:
                                company_info["Chủ sở hữu"] = value
                            elif "Tình trạng" in header:
                                company_info["Tình trạng hoạt động"] = value
                                company_info["Tình trạng"] = value
                            elif "Nơi đăng ký quản lý" in header:
                                company_info["Nơi đăng ký quản lý"] = value
                                company_info["Quản lý bởi"] = value
                            elif "Ngày cấp" in header or "Ngày hoạt động" in header:
                                company_info["Ngày cấp giấy phép"] = value
                                company_info["Ngày hoạt động"] = value
                            elif "Ngành nghề chính" in header:
                                company_info["Ngành nghề chính"] = value
                            elif "Ngành nghề kinh doanh" in header:
                                company_info["Ngành nghề kinh doanh"] = value
                            elif "Điện thoại" in header:
                                company_info["Điện thoại"] = value
                            elif "Lưu ý" in header:
                                company_info["Lưu ý"] = value

                # Kiểm tra xem có lấy được thông tin đầy đủ không
                if any(value for key, value in company_info.items() if key != "Mã số thuế"):
                    print("Thông tin công ty từ masothue.com:", company_info)
                    return company_info

            # Bước 2: Nếu không lấy được từ masothue.com, thử congtydoanhnghiep.com
            print("Không tìm thấy thông tin trên masothue.com, thử congtydoanhnghiep.com...")
            url_congty = f"https://congtydoanhnghiep.com/{formatted_name}"
            print(f"Đang truy cập URL congtydoanhnghiep.com: {url_congty}")
            response = scraper.get(url_congty, headers=self.headers)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Tìm thông tin trong bảng
                tables = soup.find_all('table', class_='table')
                for table in tables:
                    rows = table.find_all('tr')
                    for row in rows:
                        th = row.find('th')
                        td = row.find('td')
                        if th and td:
                            header = th.text.strip()
                            value = td.text.strip()
                            
                            if "Tên công ty" in header:
                                company_info["Tên công ty"] = value
                            elif "Tên Tiếng Anh" in header or "Tên quốc tế" in header:
                                company_info["Tên Tiếng Anh"] = value
                            elif "Địa Chỉ" in header or "Địa chỉ" in header:
                                company_info["Địa chỉ"] = value
                            elif "Người đại diện" in header:
                                company_info["Người đại diện"] = value
                            elif "Chủ sở hữu" in header:
                                company_info["Chủ sở hữu"] = value
                            elif "Tình trạng" in header:
                                company_info["Tình trạng hoạt động"] = value
                                company_info["Tình trạng"] = value
                            elif "Nơi đăng ký quản lý" in header:
                                company_info["Nơi đăng ký quản lý"] = value
                                company_info["Quản lý bởi"] = value
                            elif "Ngày cấp" in header or "Ngày cấp giấy phép" in header:
                                company_info["Ngày cấp giấy phép"] = value
                                company_info["Ngày hoạt động"] = value
                            elif "Ngành nghề chính" in header:
                                company_info["Ngành nghề chính"] = value
                            elif "Ngành nghề kinh doanh" in header:
                                company_info["Ngành nghề kinh doanh"] = value
                            elif "Điện thoại" in header:
                                company_info["Điện thoại"] = value
                            elif "Lưu ý" in header:
                                company_info["Lưu ý"] = value

                # Kiểm tra xem có lấy được thông tin không
                if any(value for key, value in company_info.items() if key != "Mã số thuế"):
                    print("Thông tin công ty từ congtydoanhnghiep.com:", company_info)
                    return company_info

            # Nếu không lấy được thông tin từ cả hai nguồn
            print("Không tìm thấy thông tin công ty từ bất kỳ nguồn nào")
            return None

        except Exception as e:
            print(f"Lỗi khi lấy thông tin công ty: {str(e)}")
            return None

    def search_mst(self):
        mst = self.mst_entry.get().strip()
        if not mst:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập MST!")
            return

        try:
            self.progress.start()
            
            # Xóa dữ liệu cũ
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Thêm thông báo đang xử lý
            self.tree.insert("", tk.END, values=("Đang xử lý...",) * 15)
            self.root.update()

            # Bước 1: Lấy tên công ty đã format
            formatted_name = self.get_company_name(mst)
            if not formatted_name:
                self.progress.stop()
                for item in self.tree.get_children():
                    self.tree.delete(item)
                messagebox.showinfo("Thông báo", "Không tìm thấy thông tin công ty.")
                return

            # Bước 2: Lấy thông tin chi tiết
            company_info = self.get_company_info(mst, formatted_name)
            
            # Xóa thông báo đang xử lý
            for item in self.tree.get_children():
                self.tree.delete(item)

            if company_info:
                self.tree.insert("", tk.END, values=(
                    company_info["Mã số thuế"],
                    company_info["Tên công ty"],
                    company_info["Tên Tiếng Anh"],
                    company_info["Địa chỉ"],
                    company_info["Người đại diện"],
                    company_info["Chủ sở hữu"],
                    company_info["Tình trạng hoạt động"],
                    company_info["Nơi đăng ký quản lý"],
                    company_info["Ngày cấp giấy phép"],
                    company_info["Ngày hoạt động"],
                    company_info["Ngành nghề chính"],
                    company_info["Ngành nghề kinh doanh"],
                    company_info["Lưu ý"],
                    company_info["Tình trạng"],
                    company_info["Quản lý bởi"],
                    company_info["Điện thoại"]
                ))
            else:
                messagebox.showinfo("Thông báo", "Không thể lấy thông tin chi tiết công ty.")

        except Exception as e:
            messagebox.showerror("Lỗi", f"Có lỗi xảy ra: {str(e)}")
        finally:
            self.progress.stop()

    def create_widgets(self):
        # Frame nhập liệu
        input_frame = ttk.Frame(self.root, padding="10")
        input_frame.pack(fill=tk.X)

        # Label và Entry để nhập MST
        ttk.Label(input_frame, text="Nhập MST:").pack(side=tk.LEFT)
        self.mst_entry = ttk.Entry(input_frame, width=30)
        self.mst_entry.pack(side=tk.LEFT, padx=5)

        # Nút tìm kiếm
        ttk.Button(input_frame, text="Tra cứu", command=self.search_mst).pack(side=tk.LEFT, padx=5)

        # Progress bar
        self.progress = ttk.Progressbar(input_frame, mode='indeterminate')
        self.progress.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # Treeview để hiển thị kết quả
        columns = (
            "MST", "Tên công ty", "Tên Tiếng Anh", "Địa chỉ", "Người đại diện",
            "Chủ sở hữu", "Tình trạng hoạt động", "Nơi đăng ký quản lý",
            "Ngày cấp giấy phép", "Ngày hoạt động", "Ngành nghề chính",
            "Ngành nghề kinh doanh", "Lưu ý", "Tình trạng", "Quản lý bởi", "Điện thoại"
        )
        self.tree = ttk.Treeview(self.root, columns=columns, show='headings')
        
        # Đặt tiêu đề cho các cột
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)  # Giảm chiều rộng cột để phù hợp với màn hình
        
        # Thêm scrollbar
        scrollbar = ttk.Scrollbar(self.root, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10, side=tk.LEFT)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

if __name__ == "__main__":
    root = tk.Tk()
    app = MaSoThueApp(root)
    root.mainloop()