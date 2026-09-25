using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Ink;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Shapes;
using System.Runtime.InteropServices;
using System.Windows.Interop;
using Path = System.Windows.Shapes.Path;

namespace StayXCapture.Wpf.Windows
{
    public interface IEditorAction
    {
        void Undo();
        void Redo();
    }

    public class InkStrokeAction : IEditorAction
    {
        private readonly InkCanvas _canvas;
        private readonly Stroke _stroke;
        public InkStrokeAction(InkCanvas canvas, Stroke stroke) { _canvas = canvas; _stroke = stroke; }
        public void Undo() { _canvas.Strokes.Remove(_stroke); }
        public void Redo() { if (!_canvas.Strokes.Contains(_stroke)) _canvas.Strokes.Add(_stroke); }
    }

    public class ShapeAction : IEditorAction
    {
        private readonly Canvas _canvas;
        private readonly UIElement _element;
        public ShapeAction(Canvas canvas, UIElement element) { _canvas = canvas; _element = element; }
        public void Undo() { _canvas.Children.Remove(_element); }
        public void Redo() { if (!_canvas.Children.Contains(_element)) _canvas.Children.Add(_element); }
    }

    public partial class EditorWindow : Window
    {
        private readonly BitmapSource _bitmap;
        private string _activeTool = "Pen";
        
        // Colors and styles
        private Color _selectedColor = Color.FromRgb(239, 68, 68); // #EF4444 Red
        private SolidColorBrush _selectedBrush = new SolidColorBrush(Color.FromRgb(239, 68, 68));
        private double _selectedThickness = 4.0;

        // Shape drawing state
        private bool _isDrawingShape = false;
        private Point _startPoint;
        private Shape? _currentShape;
        private Rectangle? _blurPreviewRect;
        private TextBox? _activeTextBox;

        // History
        private readonly Stack<IEditorAction> _undoStack = new();
        private readonly Stack<IEditorAction> _redoStack = new();

        // Zoom & Pan state
        private double _currentZoom = 1.0;
        private Point _panStartMouse;
        private Point _panStartOffset;
        private bool _isPanning = false;

        public EditorWindow(BitmapSource bitmap)
        {
            InitializeComponent();
            _bitmap = bitmap;
            BaseImage.Source = _bitmap;
            
            CanvasContainer.Width = _bitmap.PixelWidth;
            CanvasContainer.Height = _bitmap.PixelHeight;
            DrawingCanvas.Width = _bitmap.PixelWidth;
            DrawingCanvas.Height = _bitmap.PixelHeight;
            ShapesCanvas.Width = _bitmap.PixelWidth;
            ShapesCanvas.Height = _bitmap.PixelHeight;

            TxtImageInfo.Text = $"{_bitmap.PixelWidth} × {_bitmap.PixelHeight} px  •  100%";

            // Hook ink stroke collection for Undo
            DrawingCanvas.StrokeCollected += (s, e) =>
            {
                RecordAction(new InkStrokeAction(DrawingCanvas, e.Stroke));
            };

            // Set initial color and thickness
            _selectedColor = Color.FromRgb(239, 68, 68); // Red
            _selectedBrush = new SolidColorBrush(_selectedColor);
            _selectedThickness = 4.0;
            if (CurrentColorCircle != null) CurrentColorCircle.Background = _selectedBrush;
            if (TxtCurrentThickness != null) TxtCurrentThickness.Text = "4px";
            UpdateDrawingAttributes();

            SetTool("Pen");
        }

        private void Window_Loaded(object sender, RoutedEventArgs e)
        {
            Dispatcher.BeginInvoke(new Action(() =>
            {
                FitToScreen();
            }), System.Windows.Threading.DispatcherPriority.Loaded);
        }

        public void FitToScreen()
        {
            if (_bitmap == null || ImageScrollViewer.ActualWidth <= 0 || ImageScrollViewer.ActualHeight <= 0) return;

            double availWidth = ImageScrollViewer.ActualWidth - 64;
            double availHeight = ImageScrollViewer.ActualHeight - 64;

            if (availWidth <= 50 || availHeight <= 50) return;

            double scaleX = availWidth / _bitmap.PixelWidth;
            double scaleY = availHeight / _bitmap.PixelHeight;
            double fitScale = Math.Min(scaleX, scaleY);

            if (fitScale < 1.0)
            {
                SetZoom(fitScale);
            }
            else
            {
                SetZoom(1.0);
            }
        }

        public void SetZoom(double zoom)
        {
            _currentZoom = Math.Clamp(zoom, 0.1, 5.0);
            ZoomTransform.ScaleX = _currentZoom;
            ZoomTransform.ScaleY = _currentZoom;
            UpdateZoomDisplay();
        }

        private void UpdateZoomDisplay()
        {
            if (BtnZoomValue != null)
            {
                BtnZoomValue.Content = $"{Math.Round(_currentZoom * 100)}%";
            }
            if (TxtImageInfo != null)
            {
                TxtImageInfo.Text = $"{_bitmap.PixelWidth} × {_bitmap.PixelHeight} px  •  {Math.Round(_currentZoom * 100)}%";
            }
        }

        private void ZoomIn_Click(object sender, RoutedEventArgs e)
        {
            SetZoom(_currentZoom * 1.2);
        }

        private void ZoomOut_Click(object sender, RoutedEventArgs e)
        {
            SetZoom(_currentZoom / 1.2);
        }

        private void ZoomReset_Click(object sender, RoutedEventArgs e)
        {
            SetZoom(1.0);
        }

        private void ZoomFit_Click(object sender, RoutedEventArgs e)
        {
            FitToScreen();
        }

        private void ScrollViewer_PreviewMouseWheel(object sender, MouseWheelEventArgs e)
        {
            e.Handled = true;

            double factor = e.Delta > 0 ? 1.15 : (1.0 / 1.15);
            double oldZoom = _currentZoom;
            double newZoom = Math.Clamp(_currentZoom * factor, 0.1, 5.0);

            if (Math.Abs(newZoom - oldZoom) < 0.001) return;

            Point mouseOnViewport = e.GetPosition(ImageScrollViewer);
            double hOffset = ImageScrollViewer.HorizontalOffset;
            double vOffset = ImageScrollViewer.VerticalOffset;

            double mouseInContentX = hOffset + mouseOnViewport.X;
            double mouseInContentY = vOffset + mouseOnViewport.Y;

            _currentZoom = newZoom;
            ZoomTransform.ScaleX = _currentZoom;
            ZoomTransform.ScaleY = _currentZoom;
            UpdateZoomDisplay();

            ImageScrollViewer.UpdateLayout();

            double ratio = newZoom / oldZoom;
            double newHOffset = mouseInContentX * ratio - mouseOnViewport.X;
            double newVOffset = mouseInContentY * ratio - mouseOnViewport.Y;

            ImageScrollViewer.ScrollToHorizontalOffset(newHOffset);
            ImageScrollViewer.ScrollToVerticalOffset(newVOffset);
        }

        private void ScrollViewer_PreviewMouseDown(object sender, MouseButtonEventArgs e)
        {
            if (e.MiddleButton == MouseButtonState.Pressed || (Keyboard.IsKeyDown(Key.Space) && e.LeftButton == MouseButtonState.Pressed))
            {
                _isPanning = true;
                _panStartMouse = e.GetPosition(this);
                _panStartOffset = new Point(ImageScrollViewer.HorizontalOffset, ImageScrollViewer.VerticalOffset);
                ImageScrollViewer.CaptureMouse();
                ImageScrollViewer.Cursor = Cursors.SizeAll;
                e.Handled = true;
            }
        }

        private void ScrollViewer_PreviewMouseMove(object sender, MouseEventArgs e)
        {
            if (_isPanning)
            {
                var currentMouse = e.GetPosition(this);
                var deltaX = currentMouse.X - _panStartMouse.X;
                var deltaY = currentMouse.Y - _panStartMouse.Y;

                ImageScrollViewer.ScrollToHorizontalOffset(_panStartOffset.X - deltaX);
                ImageScrollViewer.ScrollToVerticalOffset(_panStartOffset.Y - deltaY);
                e.Handled = true;
            }
        }

        private void ScrollViewer_PreviewMouseUp(object sender, MouseButtonEventArgs e)
        {
            if (_isPanning && (e.MiddleButton == MouseButtonState.Released || e.LeftButton == MouseButtonState.Released))
            {
                _isPanning = false;
                ImageScrollViewer.ReleaseMouseCapture();
                ImageScrollViewer.Cursor = Cursors.Arrow;
                e.Handled = true;
            }
        }

        private void RecordAction(IEditorAction action)
        {
            _undoStack.Push(action);
            _redoStack.Clear();
            UpdateUndoRedoState();
        }

        private void Undo_Click(object sender, RoutedEventArgs e)
        {
            Undo();
        }

        private void Redo_Click(object sender, RoutedEventArgs e)
        {
            Redo();
        }

        private void Undo()
        {
            FinalizeText();
            if (_undoStack.Count > 0)
            {
                var action = _undoStack.Pop();
                action.Undo();
                _redoStack.Push(action);
                UpdateUndoRedoState();
            }
        }

        private void Redo()
        {
            FinalizeText();
            if (_redoStack.Count > 0)
            {
                var action = _redoStack.Pop();
                action.Redo();
                _undoStack.Push(action);
                UpdateUndoRedoState();
            }
        }

        private void UpdateUndoRedoState()
        {
            BtnUndo.IsEnabled = _undoStack.Count > 0;
            BtnRedo.IsEnabled = _redoStack.Count > 0;
            BtnUndo.Opacity = _undoStack.Count > 0 ? 1.0 : 0.4;
            BtnRedo.Opacity = _redoStack.Count > 0 ? 1.0 : 0.4;
        }

        private void Color_Select_Click(object sender, RoutedEventArgs e)
        {
            if (sender is Button btn && btn.Tag is string hex)
            {
                try
                {
                    _selectedColor = (Color)ColorConverter.ConvertFromString(hex);
                    _selectedBrush = new SolidColorBrush(_selectedColor);
                    
                    if (CurrentColorCircle != null)
                    {
                        CurrentColorCircle.Background = _selectedBrush;
                    }

                    UpdateDrawingAttributes();

                    if (_activeTextBox != null)
                    {
                        _activeTextBox.Foreground = _selectedBrush;
                    }

                    BtnColorDropdown.IsChecked = false;
                }
                catch { }
            }
        }

        private void Thickness_Select_Click(object sender, RoutedEventArgs e)
        {
            if (sender is Button btn && btn.Tag is string thickStr && double.TryParse(thickStr, out double t))
            {
                _selectedThickness = t;
                if (TxtCurrentThickness != null)
                {
                    TxtCurrentThickness.Text = $"{t}px";
                }
                UpdateDrawingAttributes();

                BtnThicknessDropdown.IsChecked = false;
            }
        }

        private void Tool_Checked(object sender, RoutedEventArgs e)
        {
            if (sender is RadioButton btn && btn.Tag is string tool)
            {
                SetTool(tool);
            }
        }

        private void SetTool(string tool)
        {
            _activeTool = tool;
            
            // Handle active textbox from previous tool
            if (_activeTool != "Text" && _activeTextBox != null)
            {
                FinalizeText();
            }

            if (tool == "Pen" || tool == "Highlight" || tool == "Eraser")
            {
                DrawingCanvas.IsHitTestVisible = true;
                ShapesCanvas.IsHitTestVisible = false;
                
                if (tool == "Eraser")
                {
                    DrawingCanvas.EditingMode = InkCanvasEditingMode.EraseByStroke;
                }
                else
                {
                    DrawingCanvas.EditingMode = InkCanvasEditingMode.Ink;
                    UpdateDrawingAttributes();
                }
            }
            else
            {
                DrawingCanvas.IsHitTestVisible = false;
                ShapesCanvas.IsHitTestVisible = true;
                ShapesCanvas.Cursor = Cursors.Cross;
            }
        }

        private void UpdateDrawingAttributes()
        {
            var attributes = new DrawingAttributes();
            if (_activeTool == "Highlight")
            {
                attributes.Color = Color.FromArgb(120, _selectedColor.R, _selectedColor.G, _selectedColor.B);
                attributes.Width = Math.Max(16, _selectedThickness * 4);
                attributes.Height = Math.Max(16, _selectedThickness * 4);
                attributes.IsHighlighter = true;
            }
            else
            {
                attributes.Color = _selectedColor;
                attributes.Width = _selectedThickness;
                attributes.Height = _selectedThickness;
                attributes.IsHighlighter = false;
            }
            DrawingCanvas.DefaultDrawingAttributes = attributes;
        }

        private void ShapesCanvas_MouseDown(object sender, MouseButtonEventArgs e)
        {
            if (e.LeftButton == MouseButtonState.Pressed)
            {
                if (_activeTool == "Text")
                {
                    if (_activeTextBox != null)
                    {
                        FinalizeText();
                        return;
                    }

                    _startPoint = e.GetPosition(ShapesCanvas);
                    _activeTextBox = new TextBox
                    {
                        Foreground = _selectedBrush,
                        Background = new SolidColorBrush(Color.FromArgb(80, 0, 0, 0)),
                        BorderThickness = new Thickness(1.5),
                        BorderBrush = new SolidColorBrush(Color.FromRgb(56, 189, 248)),
                        FontSize = Math.Max(16, _selectedThickness * 5),
                        FontWeight = FontWeights.Bold,
                        AcceptsReturn = true,
                        MinWidth = 80,
                        Padding = new Thickness(4)
                    };
                    
                    Canvas.SetLeft(_activeTextBox, _startPoint.X);
                    Canvas.SetTop(_activeTextBox, _startPoint.Y);
                    ShapesCanvas.Children.Add(_activeTextBox);
                    
                    Dispatcher.InvokeAsync(() => {
                        _activeTextBox.Focus();
                        Keyboard.Focus(_activeTextBox);
                    });
                }
                else if (_activeTool == "Rectangle" || _activeTool == "Arrow")
                {
                    _isDrawingShape = true;
                    _startPoint = e.GetPosition(ShapesCanvas);
                    
                    if (_activeTool == "Rectangle")
                    {
                        _currentShape = new Rectangle
                        {
                            Stroke = _selectedBrush,
                            StrokeThickness = _selectedThickness,
                            Fill = Brushes.Transparent
                        };
                        Canvas.SetLeft(_currentShape, _startPoint.X);
                        Canvas.SetTop(_currentShape, _startPoint.Y);
                    }
                    else if (_activeTool == "Arrow")
                    {
                        _currentShape = new Path
                        {
                            Stroke = _selectedBrush,
                            StrokeThickness = _selectedThickness,
                            Fill = _selectedBrush
                        };
                    }
                    
                    ShapesCanvas.Children.Add(_currentShape);
                    ShapesCanvas.CaptureMouse();
                }
                else if (_activeTool == "Blur")
                {
                    _isDrawingShape = true;
                    _startPoint = e.GetPosition(ShapesCanvas);

                    _blurPreviewRect = new Rectangle
                    {
                        Stroke = new SolidColorBrush(Color.FromArgb(200, 56, 189, 248)),
                        StrokeDashArray = new DoubleCollection { 3, 2 },
                        StrokeThickness = 1.5,
                        Fill = new SolidColorBrush(Color.FromArgb(50, 56, 189, 248))
                    };
                    Canvas.SetLeft(_blurPreviewRect, _startPoint.X);
                    Canvas.SetTop(_blurPreviewRect, _startPoint.Y);
                    ShapesCanvas.Children.Add(_blurPreviewRect);
                    ShapesCanvas.CaptureMouse();
                }
            }
        }

        private void ShapesCanvas_MouseMove(object sender, MouseEventArgs e)
        {
            if (_isDrawingShape)
            {
                var pos = e.GetPosition(ShapesCanvas);

                if (_activeTool == "Rectangle" && _currentShape is Rectangle rect)
                {
                    var x = Math.Min(pos.X, _startPoint.X);
                    var y = Math.Min(pos.Y, _startPoint.Y);
                    var w = Math.Abs(pos.X - _startPoint.X);
                    var h = Math.Abs(pos.Y - _startPoint.Y);

                    Canvas.SetLeft(rect, x);
                    Canvas.SetTop(rect, y);
                    rect.Width = w;
                    rect.Height = h;
                }
                else if (_activeTool == "Arrow" && _currentShape is Path path)
                {
                    Vector dir = pos - _startPoint;
                    if (dir.Length > 2)
                    {
                        dir.Normalize();
                        double arrowSize = Math.Max(12, _selectedThickness * 4);
                        Point arrowBase = pos - dir * arrowSize;
                        Vector ortho = new Vector(-dir.Y, dir.X) * (arrowSize * 0.45);
                        Point p1 = arrowBase + ortho;
                        Point p2 = arrowBase - ortho;

                        var geometry = new StreamGeometry();
                        using (var ctx = geometry.Open())
                        {
                            ctx.BeginFigure(_startPoint, false, false);
                            ctx.LineTo(pos, true, true);
                            ctx.BeginFigure(pos, true, true);
                            ctx.LineTo(p1, true, true);
                            ctx.LineTo(p2, true, true);
                        }
                        geometry.Freeze();
                        path.Data = geometry;
                    }
                }
                else if (_activeTool == "Blur" && _blurPreviewRect != null)
                {
                    var x = Math.Min(pos.X, _startPoint.X);
                    var y = Math.Min(pos.Y, _startPoint.Y);
                    var w = Math.Abs(pos.X - _startPoint.X);
                    var h = Math.Abs(pos.Y - _startPoint.Y);

                    Canvas.SetLeft(_blurPreviewRect, x);
                    Canvas.SetTop(_blurPreviewRect, y);
                    _blurPreviewRect.Width = w;
                    _blurPreviewRect.Height = h;
                }
            }
        }

        private void ShapesCanvas_MouseUp(object sender, MouseButtonEventArgs e)
        {
            if (_isDrawingShape)
            {
                _isDrawingShape = false;
                ShapesCanvas.ReleaseMouseCapture();

                if (_activeTool == "Blur" && _blurPreviewRect != null)
                {
                    double x = Canvas.GetLeft(_blurPreviewRect);
                    double y = Canvas.GetTop(_blurPreviewRect);
                    double w = _blurPreviewRect.Width;
                    double h = _blurPreviewRect.Height;

                    ShapesCanvas.Children.Remove(_blurPreviewRect);
                    _blurPreviewRect = null;

                    int cropX = Math.Max(0, (int)x);
                    int cropY = Math.Max(0, (int)y);
                    int cropW = Math.Min((int)w, _bitmap.PixelWidth - cropX);
                    int cropH = Math.Min((int)h, _bitmap.PixelHeight - cropY);

                    if (cropW >= 6 && cropH >= 6)
                    {
                        var cropped = new CroppedBitmap(_bitmap, new Int32Rect(cropX, cropY, cropW, cropH));
                        // Downscale by factor of ~8 to 12 for pixelated mosaic effect
                        double blockSize = Math.Max(8.0, Math.Min(cropW, cropH) / 6.0);
                        double scaleFactor = 1.0 / blockSize;

                        var downscaled = new TransformedBitmap(cropped, new ScaleTransform(scaleFactor, scaleFactor));
                        
                        var pixelatedImg = new Image
                        {
                            Source = downscaled,
                            Width = cropW,
                            Height = cropH,
                            Stretch = Stretch.Fill
                        };
                        RenderOptions.SetBitmapScalingMode(pixelatedImg, BitmapScalingMode.NearestNeighbor);
                        Canvas.SetLeft(pixelatedImg, cropX);
                        Canvas.SetTop(pixelatedImg, cropY);

                        ShapesCanvas.Children.Add(pixelatedImg);
                        RecordAction(new ShapeAction(ShapesCanvas, pixelatedImg));
                    }
                }
                else if (_currentShape != null)
                {
                    RecordAction(new ShapeAction(ShapesCanvas, _currentShape));
                    _currentShape = null;
                }
            }
        }

        private void FinalizeText()
        {
            if (_activeTextBox != null)
            {
                string text = _activeTextBox.Text;
                double left = Canvas.GetLeft(_activeTextBox);
                double top = Canvas.GetTop(_activeTextBox);
                ShapesCanvas.Children.Remove(_activeTextBox);

                if (!string.IsNullOrWhiteSpace(text))
                {
                    var textBlock = new TextBlock
                    {
                        Text = text,
                        Foreground = _activeTextBox.Foreground,
                        FontSize = _activeTextBox.FontSize,
                        FontWeight = _activeTextBox.FontWeight,
                        TextWrapping = TextWrapping.Wrap
                    };
                    
                    Canvas.SetLeft(textBlock, left);
                    Canvas.SetTop(textBlock, top);
                    
                    ShapesCanvas.Children.Add(textBlock);
                    RecordAction(new ShapeAction(ShapesCanvas, textBlock));
                }
                _activeTextBox = null;
            }
        }

        private RenderTargetBitmap RenderAnnotatedBitmap()
        {
            FinalizeText();

            // Temporarily reset LayoutTransform to identity so export is always 100% native unscaled resolution
            var prevTransform = CanvasContainer.LayoutTransform;
            try
            {
                CanvasContainer.LayoutTransform = Transform.Identity;
                CanvasContainer.UpdateLayout();

                int width = _bitmap.PixelWidth;
                int height = _bitmap.PixelHeight;

                RenderTargetBitmap rtb = new RenderTargetBitmap(width, height, 96d, 96d, PixelFormats.Pbgra32);
                rtb.Render(CanvasContainer);
                return rtb;
            }
            finally
            {
                CanvasContainer.LayoutTransform = prevTransform;
                CanvasContainer.UpdateLayout();
            }
        }

        private void Save_Click(object sender, RoutedEventArgs e)
        {
            var rtb = RenderAnnotatedBitmap();
            var encoder = new PngBitmapEncoder();
            encoder.Frames.Add(BitmapFrame.Create(rtb));

            var saveDialog = new Microsoft.Win32.SaveFileDialog
            {
                Filter = "PNG Image|*.png|JPEG Image|*.jpg",
                DefaultExt = "png",
                FileName = $"Capture_{DateTime.Now:yyyy-MM-dd_HH-mm-ss}.png"
            };

            if (saveDialog.ShowDialog() == true)
            {
                using (var fs = System.IO.File.OpenWrite(saveDialog.FileName))
                {
                    encoder.Save(fs);
                }
                this.Close();
            }
        }

        private void Copy_Click(object sender, RoutedEventArgs e)
        {
            var rtb = RenderAnnotatedBitmap();
            Clipboard.SetImage(rtb);
            this.Close();
        }

        private async void Upload_Click(object sender, RoutedEventArgs e)
        {
            BtnUpload.IsEnabled = false;
            BtnUpload.Content = "Uploading...";

            try
            {
                var rtb = RenderAnnotatedBitmap();
                var encoder = new PngBitmapEncoder();
                encoder.Frames.Add(BitmapFrame.Create(rtb));

                using var ms = new MemoryStream();
                encoder.Save(ms);
                byte[] bytes = ms.ToArray();

                var config = Services.ConfigService.Current;
                string apiKey = !string.IsNullOrWhiteSpace(config.CustomApiKey) ? config.CustomApiKey : config.DMarketApiKey;
                string endpoint = !string.IsNullOrWhiteSpace(config.CustomApiEndpoint) ? config.CustomApiEndpoint : "https://dmarket.space/api/upload";
                string? url = await Services.ApiService.UploadImageAsync(bytes, endpoint, apiKey);

                if (!string.IsNullOrWhiteSpace(url))
                {
                    Clipboard.SetText(url);
                    Services.HistoryService.Add(new Services.HistoryItem
                    {
                        Type = "link",
                        Data = url,
                        Timestamp = DateTime.Now.ToString("g")
                    });

                    MessageBox.Show($"Uploaded successfully!\nLink copied to clipboard:\n\n{url}", "StayX Capture", MessageBoxButton.OK, MessageBoxImage.Information);
                    this.Close();
                }
                else
                {
                    MessageBox.Show("Upload failed: No URL returned from API endpoint. Check your API settings.", "StayX Capture", MessageBoxButton.OK, MessageBoxImage.Warning);
                    BtnUpload.IsEnabled = true;
                    BtnUpload.Content = "☁ Upload";
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Upload error: {ex.Message}", "StayX Capture", MessageBoxButton.OK, MessageBoxImage.Error);
                BtnUpload.IsEnabled = true;
                BtnUpload.Content = "☁ Upload";
            }
        }

        private void Discard_Click(object sender, RoutedEventArgs e)
        {
            this.Close();
        }

        private void Window_KeyDown(object sender, KeyEventArgs e)
        {
            bool isCtrl = (Keyboard.Modifiers & ModifierKeys.Control) == ModifierKeys.Control;
            bool isShift = (Keyboard.Modifiers & ModifierKeys.Shift) == ModifierKeys.Shift;

            if (isCtrl && e.Key == Key.Z)
            {
                Undo();
                e.Handled = true;
            }
            else if ((isCtrl && e.Key == Key.Y) || (isCtrl && isShift && e.Key == Key.Z))
            {
                Redo();
                e.Handled = true;
            }
            else if (isCtrl && e.Key == Key.S)
            {
                Save_Click(sender, e);
                e.Handled = true;
            }
            else if (isCtrl && e.Key == Key.C && _activeTextBox == null)
            {
                Copy_Click(sender, e);
                e.Handled = true;
            }
            else if (isCtrl && e.Key == Key.U)
            {
                Upload_Click(sender, e);
                e.Handled = true;
            }
            else if (isCtrl && (e.Key == Key.OemPlus || e.Key == Key.Add))
            {
                ZoomIn_Click(sender, e);
                e.Handled = true;
            }
            else if (isCtrl && (e.Key == Key.OemMinus || e.Key == Key.Subtract))
            {
                ZoomOut_Click(sender, e);
                e.Handled = true;
            }
            else if (isCtrl && (e.Key == Key.D0 || e.Key == Key.NumPad0))
            {
                ZoomFit_Click(sender, e);
                e.Handled = true;
            }
            else if (isCtrl && (e.Key == Key.D1 || e.Key == Key.NumPad1))
            {
                ZoomReset_Click(sender, e);
                e.Handled = true;
            }
            else if (e.Key == Key.Escape)
            {
                if (_activeTextBox != null)
                {
                    ShapesCanvas.Children.Remove(_activeTextBox);
                    _activeTextBox = null;
                }
                else
                {
                    Close();
                }
                e.Handled = true;
            }
        }

        [DllImport("dwmapi.dll")]
        private static extern int DwmSetWindowAttribute(IntPtr hwnd, int attr, ref int attrValue, int attrSize);

        protected override void OnSourceInitialized(EventArgs e)
        {
            base.OnSourceInitialized(e);
            try
            {
                var hwnd = new WindowInteropHelper(this).Handle;
                int trueValue = 1;
                // 20 = DWMWA_USE_IMMERSIVE_DARK_MODE on Win11 & Win10 2004+
                if (DwmSetWindowAttribute(hwnd, 20, ref trueValue, sizeof(int)) != 0)
                {
                    DwmSetWindowAttribute(hwnd, 19, ref trueValue, sizeof(int));
                }
            }
            catch { }
        }

        private void Window_StateChanged(object sender, EventArgs e)
        {
            if (WindowState == WindowState.Maximized)
            {
                MainRootBorder.Padding = new Thickness(7);
                if (BtnMaximize != null)
                {
                    BtnMaximize.Content = "🗗";
                    BtnMaximize.ToolTip = "Restore Down";
                }
            }
            else
            {
                MainRootBorder.Padding = new Thickness(0);
                if (BtnMaximize != null)
                {
                    BtnMaximize.Content = "🗖";
                    BtnMaximize.ToolTip = "Maximize";
                }
            }
        }

        private void BtnMinimize_Click(object sender, RoutedEventArgs e)
        {
            WindowState = WindowState.Minimized;
        }

        private void BtnMaximize_Click(object sender, RoutedEventArgs e)
        {
            WindowState = (WindowState == WindowState.Maximized) ? WindowState.Normal : WindowState.Maximized;
        }

        private void BtnClose_Click(object sender, RoutedEventArgs e)
        {
            Close();
        }

        protected override void OnClosed(EventArgs e)
        {
            base.OnClosed(e);
            BaseImage.Source = null;
            DrawingCanvas.Strokes.Clear();
            ShapesCanvas.Children.Clear();
            _undoStack.Clear();
            _redoStack.Clear();
            MemoryHelper.MinimizeMemory();
        }
    }
}
