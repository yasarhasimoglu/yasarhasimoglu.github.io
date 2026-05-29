using System;
using Autodesk.Revit.UI;

namespace RevitMcpPlugin
{
    /// <summary>
    /// Revit yüklendiğinde otomatik başlayan giriş noktası.
    /// Bir ExternalEvent (Revit ana iş parçacığına komut göndermek için) ve
    /// bir TCP soket sunucusu (MCP sunucusundan komut almak için) başlatır.
    /// </summary>
    public class App : IExternalApplication
    {
        public static RevitCommandExecutor Executor { get; private set; }
        public static ExternalEvent RevitEvent { get; private set; }
        private SocketServer _socketServer;

        // MCP sunucusu ile aynı porta bağlanır (server.py içindeki REVIT_PORT ile eşleşmeli).
        public const int Port = 5577;

        public Result OnStartup(UIControlledApplication application)
        {
            try
            {
                // Komutları Revit'in API bağlamında (ana iş parçacığı) çalıştıran köprü.
                Executor = new RevitCommandExecutor();
                RevitEvent = ExternalEvent.Create(Executor);

                // Arka planda dinleyen soket sunucusu. Gelen JSON komutlarını
                // ExternalEvent aracılığıyla Revit'e iletir.
                _socketServer = new SocketServer(Port, Executor, RevitEvent);
                _socketServer.Start();

                CreateRibbon(application);
            }
            catch (Exception ex)
            {
                TaskDialog.Show("Revit MCP", "Başlatma hatası: " + ex.Message);
                return Result.Failed;
            }

            return Result.Succeeded;
        }

        public Result OnShutdown(UIControlledApplication application)
        {
            _socketServer?.Stop();
            return Result.Succeeded;
        }

        private void CreateRibbon(UIControlledApplication application)
        {
            const string tabName = "Revit MCP";
            try { application.CreateRibbonTab(tabName); } catch { /* sekme zaten varsa yoksay */ }

            RibbonPanel panel = application.CreateRibbonPanel(tabName, "Sunucu");
            // Bilgi amaçlı salt-okunur kutu; sunucu OnStartup'ta otomatik başlar.
            if (panel.AddItem(new TextBoxData("McpStatus")) is TextBox tb)
            {
                tb.Value = "MCP aktif • port " + Port;
                tb.Enabled = false;
            }
        }
    }
}
