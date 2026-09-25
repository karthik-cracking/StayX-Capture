using System;
using System.Globalization;
using System.IO;
using System.Windows.Data;
using System.Windows.Media.Imaging;

namespace StayXCapture.Wpf.Converters
{
    public class ImagePathToThumbnailConverter : IValueConverter
    {
        public object? Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            if (value is string path && !string.IsNullOrEmpty(path) && File.Exists(path))
            {
                try
                {
                    BitmapImage image = new BitmapImage();
                    image.BeginInit();
                    image.CacheOption = BitmapCacheOption.OnLoad;
                    // Decode to a small height to save massive amounts of RAM
                    image.DecodePixelHeight = 90;
                    image.UriSource = new Uri(path);
                    image.EndInit();
                    image.Freeze(); // Freeze the image to allow garbage collection and cross-thread use
                    return image;
                }
                catch
                {
                    return null;
                }
            }
            return null;
        }

        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
        {
            throw new NotImplementedException();
        }
    }
}
