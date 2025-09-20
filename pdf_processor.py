import pdfplumber
import PyPDF2
from PyPDF2 import PdfWriter, PdfReader
from typing import List, Tuple, Dict, Optional
import re
import os
from utils import parse_brutto_amount, extract_ticket_number, format_swedish_currency


class ParkingReceiptProcessor:
    def __init__(self):
        self.pages_data = []
        self.duplicates = {}
        self.total_amount = 0.0

    def extract_page_data(self, page, page_num: int) -> Optional[Dict]:
        """Extract ticket number and brutto amount from a page"""
        try:
            text = page.extract_text()
            if not text:
                return None

            # Extract ticket number
            ticket_number = extract_ticket_number(text)
            if not ticket_number:
                return None

            # Extract brutto amount
            brutto_amount = parse_brutto_amount(text)
            if brutto_amount is None:
                brutto_amount = 0.0

            # Try to extract date/time/location (optional)
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', text)
            date = date_match.group(1) if date_match else ""

            return {
                'page_num': page_num,
                'ticket_number': ticket_number,
                'brutto_amount': brutto_amount,
                'date': date,
                'text': text[:200]  # Store first 200 chars for debugging
            }

        except Exception as e:
            print(f"Error extracting data from page {page_num}: {e}")
            return None

    def process_pdf(self, input_path: str, progress_callback=None) -> Tuple[int, int, float]:
        """
        Process PDF and extract all receipt data
        Returns: (total_receipts, unique_receipts, total_amount)
        """
        self.pages_data = []
        self.duplicates = {}

        with pdfplumber.open(input_path) as pdf:
            total_pages = len(pdf.pages)

            for i, page in enumerate(pdf.pages):
                if progress_callback:
                    progress_callback(i, total_pages)

                page_data = self.extract_page_data(page, i)
                if page_data:
                    self.pages_data.append(page_data)

        # Find and remove duplicates
        unique_data = []
        seen_tickets = set()

        for data in self.pages_data:
            ticket = data['ticket_number']
            if ticket not in seen_tickets:
                seen_tickets.add(ticket)
                unique_data.append(data)
            else:
                if ticket not in self.duplicates:
                    self.duplicates[ticket] = 2
                else:
                    self.duplicates[ticket] += 1

        # Sort by ticket number
        unique_data.sort(key=lambda x: x['ticket_number'])

        # Calculate total
        self.total_amount = sum(data['brutto_amount'] for data in unique_data)

        # Store processed data
        self.processed_data = unique_data

        return len(self.pages_data), len(unique_data), self.total_amount

    def generate_output_pdf(self, input_path: str, output_path: str, progress_callback=None) -> bool:
        """Generate output PDF with only unique, sorted receipts"""
        try:
            # Read original PDF
            reader = PdfReader(input_path)
            writer = PdfWriter()

            # Get page numbers to keep (from processed_data)
            pages_to_keep = {data['page_num'] for data in self.processed_data}

            # Sort page numbers according to ticket number order
            page_order = [data['page_num'] for data in self.processed_data]

            # Add pages in sorted order
            for i, page_num in enumerate(page_order):
                if progress_callback:
                    progress_callback(i, len(page_order))

                writer.add_page(reader.pages[page_num])

            # Write output PDF
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)

            return True

        except Exception as e:
            print(f"Error generating output PDF: {e}")
            return False

    def get_summary(self) -> Dict:
        """Get processing summary"""
        return {
            'total_receipts': len(self.pages_data),
            'unique_receipts': len(self.processed_data) if hasattr(self, 'processed_data') else 0,
            'duplicates': self.duplicates,
            'duplicate_count': sum(count - 1 for count in self.duplicates.values()),
            'total_amount': self.total_amount,
            'formatted_amount': format_swedish_currency(self.total_amount)
        }

    def export_summary_text(self, file_path: str) -> bool:
        """Export summary as text file"""
        try:
            summary = self.get_summary()

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("═" * 50 + "\n")
                f.write("       PARKING RECEIPT PROCESSING SUMMARY\n")
                f.write("═" * 50 + "\n\n")

                f.write(f"Original receipts:    {summary['total_receipts']}\n")
                f.write(f"Unique receipts:      {summary['unique_receipts']}\n")
                f.write(f"Duplicates removed:   {summary['duplicate_count']}\n\n")

                if self.duplicates:
                    f.write("Duplicate ticket numbers:\n")
                    for ticket, count in sorted(self.duplicates.items()):
                        f.write(f"  - {ticket} ({count} instances)\n")
                    f.write("\n")

                f.write(f"Total Amount:         {summary['formatted_amount']}\n")
                f.write("\n" + "═" * 50 + "\n")

                # Add detailed list if requested
                if hasattr(self, 'processed_data'):
                    f.write("\nProcessed Receipts (sorted by ticket number):\n")
                    f.write("-" * 50 + "\n")
                    for data in self.processed_data:
                        f.write(f"Ticket: {data['ticket_number']}")
                        f.write(f" | Amount: {format_swedish_currency(data['brutto_amount'])}")
                        if data['date']:
                            f.write(f" | Date: {data['date']}")
                        f.write("\n")

            return True

        except Exception as e:
            print(f"Error exporting summary: {e}")
            return False