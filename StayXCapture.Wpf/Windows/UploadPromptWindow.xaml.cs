using System;
using System.Windows;
using System.Windows.Input;
using System.Windows.Media.Imaging;

namespace StayXCapture.Wpf.Windows
{
    public partial class UploadPromptWindow : Window
    {
        public bool ShouldUpload { get; private set; } = false;

        public UploadPromptWindow(BitmapSource previewBitmap)
        {
            InitializeComponent();
            ImgPreview.Source = previewBitmap;
        }

        private void Upload_Click(object sender, RoutedEventArgs e)
        {
            ShouldUpload = true;
            this.Close();
        }

        private void Cancel_Click(object sender, RoutedEventArgs e)
        {
            ShouldUpload = false;
            this.Close();
        }

        private void Window_KeyDown(object sender, KeyEventArgs e)
        {
            if (e.Key == Key.Enter)
            {
                ShouldUpload = true;
                this.Close();
            }
            else if (e.Key == Key.Escape)
            {
                ShouldUpload = false;
                this.Close();
            }
        }

        private void Header_MouseLeftButtonDown(object sender, MouseButtonEventArgs e)
        {
            if (e.ButtonState == MouseButtonState.Pressed)
            {
                this.DragMove();
            }
        }

        protected override void OnClosed(EventArgs e)
        {
            base.OnClosed(e);
            ImgPreview.Source = null;
            MemoryHelper.MinimizeMemory();
        }
    }
}
