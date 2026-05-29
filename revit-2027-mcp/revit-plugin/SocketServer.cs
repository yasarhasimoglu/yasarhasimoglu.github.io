using System;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using Autodesk.Revit.UI;

namespace RevitMcpPlugin
{
    /// <summary>
    /// Localhost üzerinde, uzunluk-önekli (4 byte big-endian) JSON mesajları dinleyen
    /// basit TCP sunucusu. Her istek ExternalEvent ile Revit ana iş parçacığına iletilir,
    /// sonuç beklenir ve istemciye geri gönderilir.
    /// </summary>
    public class SocketServer
    {
        private readonly int _port;
        private readonly RevitCommandExecutor _executor;
        private readonly ExternalEvent _externalEvent;
        private TcpListener _listener;
        private Thread _thread;
        private volatile bool _running;

        public SocketServer(int port, RevitCommandExecutor executor, ExternalEvent externalEvent)
        {
            _port = port;
            _executor = executor;
            _externalEvent = externalEvent;
        }

        public void Start()
        {
            _running = true;
            _thread = new Thread(Loop) { IsBackground = true, Name = "RevitMcpSocket" };
            _thread.Start();
        }

        public void Stop()
        {
            _running = false;
            try { _listener?.Stop(); } catch { }
        }

        private void Loop()
        {
            _listener = new TcpListener(IPAddress.Loopback, _port);
            _listener.Start();

            while (_running)
            {
                TcpClient client = null;
                try
                {
                    client = _listener.AcceptTcpClient();
                    HandleClient(client);
                }
                catch (SocketException) { /* Stop() çağrıldığında oluşur */ }
                catch (Exception) { /* tekil istemci hatasını yut, dinlemeye devam et */ }
                finally
                {
                    try { client?.Close(); } catch { }
                }
            }
        }

        private void HandleClient(TcpClient client)
        {
            using (var stream = client.GetStream())
            {
                string request = ReadMessage(stream);
                if (request == null) return;

                string response;
                try
                {
                    // İsteği Revit ana iş parçacığında çalıştır ve sonucu bekle.
                    response = _executor.Execute(request, _externalEvent);
                }
                catch (Exception ex)
                {
                    response = "{\"success\":false,\"error\":" + JsonStr(ex.Message) + "}";
                }

                WriteMessage(stream, response);
            }
        }

        private static string ReadMessage(NetworkStream stream)
        {
            byte[] lenBuf = ReadExactly(stream, 4);
            if (lenBuf == null) return null;
            if (BitConverter.IsLittleEndian) Array.Reverse(lenBuf);
            int len = BitConverter.ToInt32(lenBuf, 0);
            if (len <= 0 || len > 64 * 1024 * 1024) return null;
            byte[] payload = ReadExactly(stream, len);
            return payload == null ? null : Encoding.UTF8.GetString(payload);
        }

        private static void WriteMessage(NetworkStream stream, string message)
        {
            byte[] payload = Encoding.UTF8.GetBytes(message);
            byte[] lenBuf = BitConverter.GetBytes(payload.Length);
            if (BitConverter.IsLittleEndian) Array.Reverse(lenBuf);
            stream.Write(lenBuf, 0, 4);
            stream.Write(payload, 0, payload.Length);
            stream.Flush();
        }

        private static byte[] ReadExactly(NetworkStream stream, int count)
        {
            byte[] buffer = new byte[count];
            int offset = 0;
            while (offset < count)
            {
                int read = stream.Read(buffer, offset, count - offset);
                if (read <= 0) return null;
                offset += read;
            }
            return buffer;
        }

        private static string JsonStr(string s)
        {
            return "\"" + (s ?? string.Empty).Replace("\\", "\\\\").Replace("\"", "\\\"")
                .Replace("\n", "\\n").Replace("\r", "\\r") + "\"";
        }
    }
}
