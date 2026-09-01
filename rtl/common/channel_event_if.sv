// Channel event handshake. Independent per-channel timestamps (S15).
// Not a timing-accurate TDC output.

interface channel_event_if #(
    parameter int CHANNEL_W = 4,
    parameter int FINE_W    = 16,
    parameter int COARSE_W  = 32
);
  logic                      valid;
  logic [CHANNEL_W-1:0]      channel;
  logic [FINE_W-1:0]         fine_code;     // encoded delay-line code, not picoseconds
  logic signed [COARSE_W-1:0] coarse_snap;
  logic [7:0]                quality_bits;

  modport in  (input  valid, channel, fine_code, coarse_snap, quality_bits);
  modport out (output valid, channel, fine_code, coarse_snap, quality_bits);
endinterface
