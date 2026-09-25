using System;
using System.Windows;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Shapes;

namespace StayXCapture.Wpf.Windows
{
    public partial class RegionSelectionWindow : Window
    {
        private Point _startPoint;
        private bool _isDragging = false;
        private RectangleGeometry? _selectionRect;
        private BitmapSource _backgroundImage;

        public event Action<BitmapSource>? RegionSelected;

        public RegionSelectionWindow(BitmapSource background)
        {
            InitializeComponent();
            _backgroundImage = background;
        }

        private void Window_Loaded(object sender, RoutedEventArgs e)
        {
            this.Left = SystemParameters.VirtualScreenLeft;
            this.Top = SystemParameters.VirtualScreenTop;
            this.Width = SystemParameters.VirtualScreenWidth;
            this.Height = SystemParameters.VirtualScreenHeight;

            // Set the background image
            var imageBrush = new ImageBrush(_backgroundImage);
            imageBrush.Stretch = Stretch.None;
            imageBrush.AlignmentX = AlignmentX.Left;
            imageBrush.AlignmentY = AlignmentY.Top;
            this.Background = imageBrush;

            // Create a CombinedGeometry to cut out the selection from the dark overlay
            var screenRect = new RectangleGeometry(new Rect(0, 0, this.Width, this.Height));
            _selectionRect = new RectangleGeometry(new Rect(0, 0, 0, 0));
            
            var combined = new CombinedGeometry(GeometryCombineMode.Exclude, screenRect, _selectionRect);
            
            var path = new Path
            {
                Fill = new SolidColorBrush(Color.FromArgb(100, 0, 0, 0)),
                Data = combined
            };
            
            OverlayCanvas.Children.Insert(0, path);
        }

        private void Window_MouseDown(object sender, MouseButtonEventArgs e)
        {
            if (e.LeftButton == MouseButtonState.Pressed)
            {
                _isDragging = true;
                _startPoint = e.GetPosition(this);
                this.CaptureMouse();
            }
        }

        private void Window_MouseMove(object sender, MouseEventArgs e)
        {
            if (_isDragging && _selectionRect != null)
            {
                var pos = e.GetPosition(this);
                
                var x = Math.Min(pos.X, _startPoint.X);
                var y = Math.Min(pos.Y, _startPoint.Y);
                var w = Math.Abs(pos.X - _startPoint.X);
                var h = Math.Abs(pos.Y - _startPoint.Y);

                _selectionRect.Rect = new Rect(x, y, w, h);
                
                // Update selection border
                SelectionPath.Data = new RectangleGeometry(_selectionRect.Rect);
            }
        }

        private void Window_MouseUp(object sender, MouseButtonEventArgs e)
        {
            if (_isDragging)
            {
                _isDragging = false;
                this.ReleaseMouseCapture();

                CroppedBitmap? cropped = null;
                if (_selectionRect != null && _backgroundImage != null)
                {
                    var rect = _selectionRect.Rect;
                    if (rect.Width > 5 && rect.Height > 5)
                    {
                        // Calculate crop bounds safely clamped to bitmap boundaries
                        int cropX = Math.Max(0, (int)rect.X);
                        int cropY = Math.Max(0, (int)rect.Y);
                        int cropW = Math.Min((int)rect.Width, _backgroundImage.PixelWidth - cropX);
                        int cropH = Math.Min((int)rect.Height, _backgroundImage.PixelHeight - cropY);

                        if (cropW > 0 && cropH > 0)
                        {
                            try
                            {
                                var cropRect = new Int32Rect(cropX, cropY, cropW, cropH);
                                cropped = new CroppedBitmap(_backgroundImage, cropRect);
                                cropped.Freeze();
                            }
                            catch (Exception ex)
                            {
                                System.Diagnostics.Debug.WriteLine($"Cropping exception: {ex.Message}");
                            }
                        }
                    }
                }
                
                // Clear memory and close overlay first so screen cleanly returns to normal
                this.Background = null;
                _backgroundImage = null!;
                OverlayCanvas.Children.Clear();
                MemoryHelper.MinimizeMemory();
                
                this.Close();

                if (cropped != null)
                {
                    RegionSelected?.Invoke(cropped);
                }
            }
        }

        private void Window_KeyDown(object sender, KeyEventArgs e)
        {
            if (e.Key == Key.Escape)
            {
                this.Background = null;
                _backgroundImage = null!;
                MemoryHelper.MinimizeMemory();
                this.Close();
            }
        }
    }
}
