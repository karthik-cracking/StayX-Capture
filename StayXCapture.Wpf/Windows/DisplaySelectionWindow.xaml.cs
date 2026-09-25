using System;
using System.Collections.Generic;
using System.Windows;
using System.Windows.Input;
using StayXCapture.Wpf.Services;

namespace StayXCapture.Wpf.Windows
{
    public class DisplayCardItem
    {
        public ScreenInfo? Screen { get; set; }
        public string DisplayNumber { get; set; } = "1";
        public string Title { get; set; } = "";
        public string Subtitle { get; set; } = "";
        public string ResolutionText { get; set; } = "";
        public bool IsAllDisplays => Screen == null;
    }

    public partial class DisplaySelectionWindow : Window
    {
        public event Action<ScreenInfo?>? DisplaySelected;
        private readonly List<DisplayCardItem> _items = new List<DisplayCardItem>();

        public DisplaySelectionWindow(List<ScreenInfo> screens)
        {
            InitializeComponent();

            int totalWidth = (int)SystemParameters.VirtualScreenWidth;
            int totalHeight = (int)SystemParameters.VirtualScreenHeight;

            foreach (var screen in screens)
            {
                _items.Add(new DisplayCardItem
                {
                    Screen = screen,
                    DisplayNumber = screen.Index.ToString(),
                    Title = screen.Title,
                    Subtitle = screen.DeviceName,
                    ResolutionText = screen.ResolutionText
                });
            }

            // Add "All Displays" option
            _items.Add(new DisplayCardItem
            {
                Screen = null,
                DisplayNumber = "ALL",
                Title = "All Displays",
                Subtitle = $"{screens.Count} Screens Combined",
                ResolutionText = $"{totalWidth} × {totalHeight}"
            });

            DisplaysItemsControl.ItemsSource = _items;
        }

        private void DisplayCard_Click(object sender, RoutedEventArgs e)
        {
            if (sender is FrameworkElement element && element.Tag is DisplayCardItem cardItem)
            {
                this.Close();
                DisplaySelected?.Invoke(cardItem.Screen);
            }
        }

        private void Cancel_Click(object sender, RoutedEventArgs e)
        {
            this.Close();
        }

        private void Window_KeyDown(object sender, KeyEventArgs e)
        {
            if (e.Key == Key.Escape)
            {
                this.Close();
            }
            else if (e.Key >= Key.D1 && e.Key <= Key.D9)
            {
                int index = e.Key - Key.D1;
                if (index < _items.Count - 1)
                {
                    this.Close();
                    DisplaySelected?.Invoke(_items[index].Screen);
                }
            }
            else if (e.Key == Key.A)
            {
                this.Close();
                DisplaySelected?.Invoke(null);
            }
        }

        private void Header_MouseLeftButtonDown(object sender, MouseButtonEventArgs e)
        {
            if (e.ButtonState == MouseButtonState.Pressed)
            {
                this.DragMove();
            }
        }
    }
}
