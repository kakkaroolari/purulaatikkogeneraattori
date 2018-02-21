using System;
using System.Diagnostics;
// output?


namespace SwecoToolbar
{
    public class Tracer
    {
        public static void _trace(String what)
        {
            var pp = "";
            try
            {
                pp = AppDomain.CurrentDomain.FriendlyName;
            }
            catch
            {
                // ignored
            }
            Debug.WriteLine("[ERITE] {0}: {1}", pp, what);
        }
    }
}
