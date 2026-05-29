using System;
using System.Text.Json;
using System.Threading;
using Autodesk.Revit.UI;

namespace RevitMcpPlugin
{
    /// <summary>
    /// IExternalEventHandler — Revit API çağrılarının çalıştırılabileceği tek güvenli yer.
    /// Soket iş parçacığı Execute() çağırır; bu metot ExternalEvent'i tetikler ve
    /// Revit ana iş parçacığında Dispatch tamamlanana kadar bloklanır.
    /// </summary>
    public class RevitCommandExecutor : IExternalEventHandler
    {
        private readonly object _lock = new object();
        private string _request;
        private string _response;
        private UIApplication _uiApp;
        private ManualResetEventSlim _done;

        /// <summary>Soket iş parçacığından çağrılır. Senkron sonuç döner.</summary>
        public string Execute(string request, ExternalEvent externalEvent)
        {
            // Aynı anda tek istek işlensin (Revit tek iş parçacıklı).
            lock (_lock)
            {
                _request = request;
                _done = new ManualResetEventSlim(false);
                externalEvent.Raise();

                // Revit'in ExternalEvent'i işlemesini bekle (en fazla 5 dk).
                if (!_done.Wait(TimeSpan.FromMinutes(5)))
                    return "{\"success\":false,\"error\":\"Zaman aşımı: Revit yanıt vermedi.\"}";

                return _response;
            }
        }

        // Revit ana iş parçacığında çalışır.
        public void Execute(UIApplication app)
        {
            _uiApp = app;
            try
            {
                using (var doc = JsonDocument.Parse(_request))
                {
                    var root = doc.RootElement;
                    string command = root.GetProperty("command").GetString();
                    JsonElement parameters = root.TryGetProperty("params", out var p)
                        ? p
                        : default;

                    object result = CommandDispatcher.Dispatch(_uiApp, command, parameters);
                    // result kök seviyede serileştirilir; böylece çalışma-zamanı
                    // (anonim) tipinin tüm alanları doğru yazılır.
                    string resultJson = JsonSerializer.Serialize(result);
                    _response = "{\"success\":true,\"result\":" + resultJson + "}";
                }
            }
            catch (Exception ex)
            {
                _response = JsonSerializer.Serialize(new { success = false, error = ex.Message });
            }
            finally
            {
                _done.Set();
            }
        }

        public string GetName() => "Revit MCP Command Executor";
    }
}
