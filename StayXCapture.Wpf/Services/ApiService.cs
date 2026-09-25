using System;
using System.IO;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Threading.Tasks;
using Newtonsoft.Json.Linq;

namespace StayXCapture.Wpf.Services
{
    public static class ApiService
    {
        private static readonly HttpClient _httpClient = new HttpClient();

        public static async Task<string?> UploadToDMarketAsync(string filePath, string apiKey)
        {
            return await UploadToCustomApiAsync(filePath, "https://dmarket.space/api/upload", apiKey);
        }

        public static async Task<string?> UploadToCustomApiAsync(string filePath, string endpoint, string apiKey)
        {
            try
            {
                var fileName = Path.GetFileName(filePath);
                var fileBytes = await File.ReadAllBytesAsync(filePath);
                return await UploadBytesToCustomApiAsync(fileBytes, endpoint, apiKey, fileName);
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Custom API Exception: {ex.Message}");
                return null;
            }
        }

        public static async Task<string?> UploadImageAsync(byte[] fileBytes, string endpoint, string apiKey, string fileName = "capture.png")
        {
            return await UploadBytesToCustomApiAsync(fileBytes, endpoint, apiKey, fileName);
        }

        public static async Task<string?> UploadBytesToCustomApiAsync(byte[] fileBytes, string endpoint, string apiKey, string fileName = "capture.png")
        {
            if (string.IsNullOrWhiteSpace(endpoint))
            {
                endpoint = "https://dmarket.space/api/upload";
            }

            if (!endpoint.StartsWith("http://", StringComparison.OrdinalIgnoreCase) && 
                !endpoint.StartsWith("https://", StringComparison.OrdinalIgnoreCase))
            {
                endpoint = "https://" + endpoint;
            }

            try
            {
                // 1. Try Multipart Form Data first
                using (var content = new MultipartFormDataContent())
                {
                    content.Add(new StringContent("screenshot"), "type");
                    content.Add(new StringContent(fileName), "filename");
                    content.Add(new StringContent(DateTime.Now.ToString("O")), "timestamp");
                    if (!string.IsNullOrWhiteSpace(apiKey))
                    {
                        content.Add(new StringContent(apiKey), "api_key");
                    }

                    var fileContent = new ByteArrayContent(fileBytes);
                    fileContent.Headers.ContentType = MediaTypeHeaderValue.Parse("image/png");
                    content.Add(fileContent, "file", fileName);

                    using var request = new HttpRequestMessage(HttpMethod.Post, endpoint)
                    {
                        Content = content
                    };

                    if (!string.IsNullOrWhiteSpace(apiKey))
                    {
                        request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", apiKey);
                        request.Headers.TryAddWithoutValidation("X-API-Key", apiKey);
                    }

                    var response = await _httpClient.SendAsync(request);

                    if (response.IsSuccessStatusCode)
                    {
                        var responseString = await response.Content.ReadAsStringAsync();
                        return ParseApiResponse(responseString);
                    }
                    else
                    {
                        System.Diagnostics.Debug.WriteLine($"Custom API Multipart error: {response.StatusCode}");
                    }
                }

                // 2. Fallback to JSON Base64 payload (standard for API_SERVER_EXAMPLES.md)
                {
                    var base64 = Convert.ToBase64String(fileBytes);
                    var payload = new JObject
                    {
                        ["type"] = "screenshot",
                        ["filename"] = fileName,
                        ["image"] = base64,
                        ["timestamp"] = DateTime.Now.ToString("O")
                    };
                    if (!string.IsNullOrWhiteSpace(apiKey))
                    {
                        payload["api_key"] = apiKey;
                    }

                    using var jsonContent = new StringContent(payload.ToString(), System.Text.Encoding.UTF8, "application/json");
                    using var request = new HttpRequestMessage(HttpMethod.Post, endpoint)
                    {
                        Content = jsonContent
                    };

                    if (!string.IsNullOrWhiteSpace(apiKey))
                    {
                        request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", apiKey);
                        request.Headers.TryAddWithoutValidation("X-API-Key", apiKey);
                    }

                    var response = await _httpClient.SendAsync(request);
                    if (response.IsSuccessStatusCode)
                    {
                        var responseString = await response.Content.ReadAsStringAsync();
                        return ParseApiResponse(responseString);
                    }
                    else
                    {
                        System.Diagnostics.Debug.WriteLine($"Custom API JSON error: {response.StatusCode} - {await response.Content.ReadAsStringAsync()}");
                    }
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Custom API Exception: {ex.Message}");
            }
            return null;
        }

        private static string? ParseApiResponse(string responseString)
        {
            if (string.IsNullOrWhiteSpace(responseString)) return null;

            responseString = responseString.Trim();
            if (responseString.StartsWith("http://", StringComparison.OrdinalIgnoreCase) || 
                responseString.StartsWith("https://", StringComparison.OrdinalIgnoreCase))
            {
                return responseString;
            }

            try
            {
                var json = JObject.Parse(responseString);
                var url = json["url"]?.ToString() 
                       ?? json["data"]?["url"]?.ToString() 
                       ?? json["link"]?.ToString() 
                       ?? json["file_url"]?.ToString();

                if (!string.IsNullOrWhiteSpace(url)) return url;
                return json["message"]?.ToString() ?? "Upload Successful";
            }
            catch
            {
                return responseString;
            }
        }

        public static async Task<string?> UploadToImgBBAsync(string filePath, string apiKey)
        {
            if (string.IsNullOrWhiteSpace(apiKey)) return null;

            try
            {
                var fileBytes = await File.ReadAllBytesAsync(filePath);
                var base64Image = Convert.ToBase64String(fileBytes);

                using (var content = new MultipartFormDataContent())
                {
                    content.Add(new StringContent(apiKey), "key");
                    content.Add(new StringContent(base64Image), "image");

                    var response = await _httpClient.PostAsync("https://api.imgbb.com/1/upload", content);

                    if (response.IsSuccessStatusCode)
                    {
                        var responseString = await response.Content.ReadAsStringAsync();
                        var json = JObject.Parse(responseString);
                        return json["data"]?["url"]?.ToString();
                    }
                    else
                    {
                        System.Diagnostics.Debug.WriteLine($"ImgBB Upload Error: {response.StatusCode} - {await response.Content.ReadAsStringAsync()}");
                    }
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"ImgBB API Exception: {ex.Message}");
            }
            return null;
        }

        public static async Task<string?> UploadToGoogleDriveAsync(string filePath, string apiKey)
        {
            // Requires OAuth2 workflow, out of scope for simple API key uploads
            // Included for future implementation
            await Task.Delay(100);
            return null;
        }
    }
}
