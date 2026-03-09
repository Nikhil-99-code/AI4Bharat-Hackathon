"""
PDF Report Generator for Agri-Nexus
Generates downloadable diagnosis reports
"""

from datetime import datetime
from typing import Dict, Optional
from io import BytesIO


try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


class PDFGenerator:
    """Generate PDF reports for crop diagnosis"""
    
    def __init__(self):
        """Initialize PDF generator"""
        if not REPORTLAB_AVAILABLE:
            raise ImportError("reportlab not installed. Run: pip install reportlab")
        
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2E7D32'),
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#1976D2'),
            spaceAfter=12,
            spaceBefore=12
        ))
        
        # Info style
        self.styles.add(ParagraphStyle(
            name='InfoText',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=6
        ))
    
    def generate_diagnosis_report(
        self,
        diagnosis_data: Dict,
        user_id: str,
        output_path: Optional[str] = None
    ) -> BytesIO:
        """
        Generate PDF report for crop diagnosis
        
        Args:
            diagnosis_data: Diagnosis information
            user_id: User identifier
            output_path: Optional file path to save PDF
            
        Returns:
            BytesIO buffer with PDF content
        """
        # Create PDF buffer
        buffer = BytesIO()
        
        # Create PDF document
        doc = SimpleDocTemplate(
            buffer if not output_path else output_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Container for PDF elements
        story = []
        
        # Title
        title = Paragraph("🌾 Agri-Nexus Crop Diagnosis Report", self.styles['CustomTitle'])
        story.append(title)
        story.append(Spacer(1, 0.2 * inch))
        
        # Report info
        report_date = datetime.now().strftime("%B %d, %Y %I:%M %p")
        info_text = f"<b>Report Date:</b> {report_date}<br/><b>User ID:</b> {user_id}"
        story.append(Paragraph(info_text, self.styles['InfoText']))
        story.append(Spacer(1, 0.3 * inch))
        
        # Diagnosis Summary
        story.append(Paragraph("Diagnosis Summary", self.styles['SectionHeader']))
        
        disease_name = diagnosis_data.get('disease_name', 'Unknown')
        confidence = diagnosis_data.get('confidence', 0)
        
        summary_data = [
            ['Disease/Issue:', disease_name],
            ['Confidence Level:', f"{confidence * 100:.1f}%"],
            ['Language:', diagnosis_data.get('language', 'en').upper()],
            ['Image:', diagnosis_data.get('image_s3_key', 'N/A').split('/')[-1]]
        ]
        
        summary_table = Table(summary_data, colWidths=[2 * inch, 4 * inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E3F2FD')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 0.3 * inch))
        
        # Treatment Recommendations
        story.append(Paragraph("Treatment Recommendations", self.styles['SectionHeader']))
        treatment = diagnosis_data.get('treatment', 'No treatment information available')
        story.append(Paragraph(treatment, self.styles['InfoText']))
        story.append(Spacer(1, 0.3 * inch))
        
        # Full Diagnosis
        if 'full_diagnosis' in diagnosis_data:
            story.append(Paragraph("Detailed Analysis", self.styles['SectionHeader']))
            full_diagnosis = diagnosis_data['full_diagnosis']
            
            # Clean up diagnosis text for PDF
            diagnosis_lines = full_diagnosis.split('\n')
            for line in diagnosis_lines[:20]:  # Limit to first 20 lines
                if line.strip():
                    story.append(Paragraph(line.strip(), self.styles['InfoText']))
            
            story.append(Spacer(1, 0.3 * inch))
        
        # Footer
        story.append(Spacer(1, 0.5 * inch))
        footer_text = """
        <para align=center>
        <font size=9 color=grey>
        This report is generated by Agri-Nexus AI Platform<br/>
        For support: support@agrinexus.in | www.agrinexus.in<br/>
        © 2024 Agri-Nexus. All rights reserved.
        </font>
        </para>
        """
        story.append(Paragraph(footer_text, self.styles['Normal']))
        
        # Build PDF
        doc.build(story)
        
        # Reset buffer position
        buffer.seek(0)
        
        return buffer
    
    def generate_alert_report(
        self,
        alerts_data: list,
        user_id: str
    ) -> BytesIO:
        """Generate PDF report for price alerts"""
        buffer = BytesIO()
        
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        story = []
        
        # Title
        title = Paragraph("📈 Agri-Nexus Price Alerts Report", self.styles['CustomTitle'])
        story.append(title)
        story.append(Spacer(1, 0.2 * inch))
        
        # Report info
        report_date = datetime.now().strftime("%B %d, %Y %I:%M %p")
        info_text = f"<b>Report Date:</b> {report_date}<br/><b>User ID:</b> {user_id}"
        story.append(Paragraph(info_text, self.styles['InfoText']))
        story.append(Spacer(1, 0.3 * inch))
        
        # Alerts table
        story.append(Paragraph("Active Price Alerts", self.styles['SectionHeader']))
        
        if alerts_data:
            table_data = [['Crop', 'Location', 'Target Price', 'Status']]
            
            for alert in alerts_data:
                table_data.append([
                    alert.get('crop_type', 'N/A').title(),
                    alert.get('location', 'N/A'),
                    f"₹{alert.get('target_price', 0)}",
                    'Active'
                ])
            
            alerts_table = Table(table_data, colWidths=[1.5 * inch, 1.5 * inch, 1.5 * inch, 1.5 * inch])
            alerts_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E7D32')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(alerts_table)
        else:
            story.append(Paragraph("No active alerts found.", self.styles['InfoText']))
        
        story.append(Spacer(1, 0.5 * inch))
        
        # Footer
        footer_text = """
        <para align=center>
        <font size=9 color=grey>
        Agri-Nexus AI Platform - Market Intelligence<br/>
        © 2024 Agri-Nexus. All rights reserved.
        </font>
        </para>
        """
        story.append(Paragraph(footer_text, self.styles['Normal']))
        
        doc.build(story)
        buffer.seek(0)
        
        return buffer


def get_pdf_generator() -> PDFGenerator:
    """Get PDF generator instance"""
    return PDFGenerator()


if __name__ == '__main__':
    # Test PDF generation
    if REPORTLAB_AVAILABLE:
        generator = get_pdf_generator()
        
        test_diagnosis = {
            'disease_name': 'Leaf Blight',
            'confidence': 0.85,
            'treatment': 'Apply fungicide and remove affected leaves',
            'image_s3_key': 'images/test/test.jpg',
            'language': 'en',
            'full_diagnosis': 'Test diagnosis with detailed information about the crop disease.'
        }
        
        pdf_buffer = generator.generate_diagnosis_report(test_diagnosis, 'test_user_001')
        
        # Save to file
        with open('test_report.pdf', 'wb') as f:
            f.write(pdf_buffer.getvalue())
        
        print("✅ Test PDF generated: test_report.pdf")
    else:
        print("❌ reportlab not installed")
