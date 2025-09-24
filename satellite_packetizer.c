/**
 * @file satellite_packetizer.c
 * @brief A unified application to packetize data for satellite communication.
 *
 * This program performs a three-stage process entirely in memory, making it
 * suitable for resource-constrained embedded systems like a BeagleBone.
 *
 * 1. AX.25 Framing: Reads a binary input file in chunks and wraps each
 * chunk in a standard AX.25 UI-frame.
 * 2. FX.25 FEC Encoding: Applies Forward Error Correction using a Reed-Solomon
 * (255, 223) code to the AX.25 frame for robustness against transmission errors.
 * 3. KISS Protocol Output: Wraps the final, error-corrected FX.25 frame
 * in the KISS protocol, which is the standard for sending packet data
 * over a serial interface to a radio transceiver.
 *
 * WHY THIS STRUCTURE:
 * - Single File: Simplifies the build process for an embedded target.
 * - In-Memory Pipeline: Avoids writing to disk (e.g., SD card/eMMC), which is
 * slow, power-intensive, and causes wear on flash storage. This is critical
 * for satellite reliability.
 * - Modularity: Functions are kept separate and testable, even in one file.
 * - Command-line Driven: Allows for flexibility without recompiling the code.
 *
 * Compile with:
 * gcc -Wall satellite_packetizer.c -o packetizer -lfec
 *
 * Run with:
 * ./packetizer <source_call> <dest_call> <input_file> <output_kiss_file>
 * Example: ./packetizer N0CALL-1 CQ big_data.bin radio_output.kiss
 */

// =============================================================================
// Includes
// =============================================================================
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <stdint.h>
#include "fec.h" // Requires libfec to be installed (e.g., sudo apt install libfec-dev)

// =============================================================================
// Global Constants and Configuration
// =============================================================================

// --- AX.25 Protocol Constants ---
#define AX25_CONTROL 0x03   // UI-Frame (Unnumbered Information)
#define PID_NOL3     0xF0   // No Layer 3 protocol

// --- FX.25 Protocol Constants ---
#define FX25_K 223 // Data bytes in a Reed-Solomon block
#define FX25_N 255 // Total bytes (data + parity) in a Reed-Solomon block
static const uint8_t CORR_TAG[8] = { 0xCC, 0x8F, 0x8A, 0xE4, 0x85, 0xE2, 0x98, 0x01 };

// --- KISS Protocol Constants ---
#define KISS_FEND 0xC0 // Frame End
#define KISS_FESC 0xDB // Frame Escape
#define KISS_TFEND 0xDC // Transposed FEND
#define KISS_TFESC 0xDD // Transposed FESC
#define KISS_CMD_DATA 0x00 // Command for Data Frame on port 0

// --- Application Constants ---
#define MAX_PAYLOAD 150 // WHY: Keep payload small enough so the final AX.25 frame is < FX25_K (223 bytes).
                        // (14 addr + 2 ctrl/pid + payload + 2 FCS) must be < 223. 150 is a safe value.

// =============================================================================
// Data Structures
// =============================================================================

/**
 * @brief Holds a callsign and its SSID.
 */
typedef struct {
    char call[8];
    uint8_t ssid;
} ax25_address_t;

/**
 * @brief Holds the handle for the Reed-Solomon encoder.
 * WHY: Encapsulating the handle in a struct makes the code cleaner and easier
 * to pass around, avoiding global variables.
 */
typedef struct {
    void* rs_handle;
} fx25_encoder_t;


// =============================================================================
// Low-Level Utility Functions
// =============================================================================

/**
 * @brief Encodes a callsign and SSID into the 7-byte AX.25 address format.
 */
void encode_address(const char* call, uint8_t ssid, uint8_t* out, int last_addr) {
    int call_len = strlen(call);
    // 1. Shift callsign chars left by 1 bit
    for (int i = 0; i < 6; i++) {
        out[i] = (i < call_len) ? (uint8_t)call[i] << 1 : (uint8_t)' ' << 1;
    }
    // 2. Encode SSID and set the final address bit if needed
    out[6] = (ssid << 1) | 0b01100000 | (last_addr ? 1 : 0);
}

/**
 * @brief Calculates the CCITT CRC-16 checksum for the AX.25 Frame Check Sequence (FCS).
 */
uint16_t calculate_crc(const uint8_t* data, int length) {
    uint16_t crc = 0xFFFF;
    for (int i = 0; i < length; i++) {
        crc ^= (uint16_t)data[i] << 8;
        for (int j = 0; j < 8; j++) {
            if (crc & 0x8000) {
                crc = (crc << 1) ^ 0x1021;
            } else {
                crc = crc << 1;
            }
        }
    }
    return crc ^ 0xFFFF;
}


// =============================================================================
// FX.25 Module (FEC Encoding)
// =============================================================================

/**
 * @brief Initializes the Reed-Solomon encoder.
 * @return Pointer to an allocated fx25_encoder_t, or NULL on failure.
 */
fx25_encoder_t* fx25_init() {
    fx25_encoder_t* encoder = malloc(sizeof(fx25_encoder_t));
    if (!encoder) return NULL; // WHY: Always check malloc results on embedded systems.

    // Initialize RS(255, 223), the standard for FX.25
    encoder->rs_handle = init_rs_char(8, 0x187, 112, 11, 32, 0);
    if (!encoder->rs_handle) {
        free(encoder);
        return NULL;
    }
    return encoder;
}

/**
 * @brief Frees all resources used by the encoder.
 */
void fx25_cleanup(fx25_encoder_t* encoder) {
    if (encoder) {
        if (encoder->rs_handle) {
            free_rs_char(encoder->rs_handle);
        }
        free(encoder);
    }
}

/**
 * @brief Encodes a complete AX.25 frame with FX.25 FEC.
 * @param ax25_frame The raw AX.25 frame (address, control, pid, payload, fcs).
 * @param ax25_len Length of the raw AX.25 frame.
 * @param fx25_frame_out Buffer to store the resulting FX.25 frame.
 * @return The total length of the FX.25 frame (8-byte tag + 255-byte codeword), or 0 on error.
 */
int fx25_encode_frame(fx25_encoder_t* encoder, const uint8_t* ax25_frame, int ax25_len, uint8_t* fx25_frame_out) {
    if (ax25_len > FX25_K) {
        fprintf(stderr, "Error: AX.25 frame too large for FX.25 (%d > %d)\n", ax25_len, FX25_K);
        return 0;
    }

    // 1. Prepend the 8-byte Correlation Tag for modem synchronization.
    memcpy(fx25_frame_out, CORR_TAG, 8);

    // 2. Prepare the Reed-Solomon block.
    uint8_t rs_block[FX25_N];
    memset(rs_block, 0, FX25_N); // WHY: Zero-pad the data portion. libfec requires the full block.
    memcpy(rs_block, ax25_frame, ax25_len);

    // 3. Calculate and add the 32 parity bytes to the end of the block.
    encode_rs_char(encoder->rs_handle, rs_block, rs_block + FX25_K);

    // 4. Copy the full 255-byte codeword to the output frame.
    memcpy(fx25_frame_out + 8, rs_block, FX25_N);

    return 8 + FX25_N;
}


// =============================================================================
// AX.25 Module (Frame Generation)
// =============================================================================

/**
 * @brief Generates a complete AX.25 UI-frame in a buffer.
 * @return The length of the generated frame, or 0 on error.
 */
int ax25_generate_ui_frame(uint8_t* frame_buffer, ax25_address_t dest, ax25_address_t src, const uint8_t* payload, int payload_len) {
    int pos = 0;

    // 1. Address Fields (Destination, then Source)
    encode_address(dest.call, dest.ssid, &frame_buffer[pos], 0);
    pos += 7;
    encode_address(src.call, src.ssid, &frame_buffer[pos], 1); // Source is the last address
    pos += 7;

    // 2. Control and PID Fields
    frame_buffer[pos++] = AX25_CONTROL;
    frame_buffer[pos++] = PID_NOL3;

    // 3. Payload
    memcpy(&frame_buffer[pos], payload, payload_len);
    pos += payload_len;

    // 4. Frame Check Sequence (FCS / CRC)
    uint16_t fcs = calculate_crc(frame_buffer, pos);
    frame_buffer[pos++] = fcs & 0xFF;         // Low byte
    frame_buffer[pos++] = (fcs >> 8) & 0xFF;  // High byte

    return pos;
}


// =============================================================================
// KISS Module (Output Formatting)
// =============================================================================

/**
 * @brief Writes a data frame to a file stream in KISS format.
 * @param stream The output stream (e.g., a file or a serial port).
 * @param frame The data to be written (our complete FX.25 frame).
 * @param length The length of the data.
 */
void write_kiss_frame(FILE* stream, const uint8_t* frame, int length) {
    fputc(KISS_FEND, stream);
    fputc(KISS_CMD_DATA, stream);

    // WHY: We must escape special characters in the data stream to prevent
    // them from being misinterpreted as a FEND or FESC byte.
    for (int i = 0; i < length; i++) {
        if (frame[i] == KISS_FEND) {
            fputc(KISS_FESC, stream);
            fputc(KISS_TFEND, stream);
        } else if (frame[i] == KISS_FESC) {
            fputc(KISS_FESC, stream);
            fputc(KISS_TFESC, stream);
        } else {
            fputc(frame[i], stream);
        }
    }
    fputc(KISS_FEND, stream);
}


// =============================================================================
// Main Application
// =============================================================================

int main(int argc, char* argv[]) {
    // --- 1. Argument Parsing ---
    if (argc < 5) {
        fprintf(stderr, "Usage: %s <source_call> <dest_call> <input_file> <output_kiss_file>\n", argv[0]);
        return 1;
    }

    // Simple parsing of callsign and SSID
    ax25_address_t src_addr = { .ssid = 0 };
    ax25_address_t dest_addr = { .ssid = 0 };
    sscanf(argv[1], "%7[^-]-%hhu", src_addr.call, &src_addr.ssid);
    sscanf(argv[2], "%7[^-]-%hhu", dest_addr.call, &dest_addr.ssid);
    const char* input_filename = argv[3];
    const char* output_filename = argv[4];

    printf("Packetizer starting...\n");
    printf("  Source: %s-%d\n", src_addr.call, src_addr.ssid);
    printf("  Destination: %s-%d\n", dest_addr.call, dest_addr.ssid);
    printf("  Input: %s\n", input_filename);
    printf("  Output: %s\n", output_filename);

    // --- 2. Initialization ---
    fx25_encoder_t* encoder = fx25_init();
    if (!encoder) {
        fprintf(stderr, "Error: Failed to initialize FX.25 encoder.\n");
        return 1;
    }

    FILE* input_file = fopen(input_filename, "rb"); // WHY: "rb" for binary read.
    if (!input_file) {
        perror("Error opening input file");
        fx25_cleanup(encoder);
        return 1;
    }

    FILE* output_file = fopen(output_filename, "wb"); // WHY: "wb" for binary write.
    if (!output_file) {
        perror("Error creating output file");
        fclose(input_file);
        fx25_cleanup(encoder);
        return 1;
    }

    // --- 3. Main Processing Loop ---
    uint8_t payload_buffer[MAX_PAYLOAD];
    uint8_t ax25_buffer[512]; // Buffer for the AX.25 frame
    uint8_t fx25_buffer[512]; // Buffer for the final FX.25 frame
    size_t bytes_read;
    int packet_count = 0;

    // WHY: Reading in chunks is memory-efficient and crucial for embedded systems.
    // We avoid loading the entire file into RAM.
    while ((bytes_read = fread(payload_buffer, 1, MAX_PAYLOAD, input_file)) > 0) {

        // Step A: Generate the raw AX.25 frame in memory
        int ax25_len = ax25_generate_ui_frame(ax25_buffer, dest_addr, src_addr, payload_buffer, bytes_read);
        if (ax25_len == 0) {
            fprintf(stderr, "Warning: Failed to generate AX.25 frame for packet %d\n", packet_count);
            continue;
        }

        // Step B: Encode the AX.25 frame with FX.25 FEC
        int fx25_len = fx25_encode_frame(encoder, ax25_buffer, ax25_len, fx25_buffer);
        if (fx25_len == 0) {
            fprintf(stderr, "Warning: Failed to FEC-encode packet %d\n", packet_count);
            continue;
        }

        // Step C: Write the final, robust frame to the output in KISS format
        write_kiss_frame(output_file, fx25_buffer, fx25_len);

        packet_count++;
    }

    // --- 4. Cleanup ---
    // WHY: Always clean up resources. On a long-running satellite application,
    // memory leaks or unclosed file handles can lead to system failure.
    fclose(input_file);
    fclose(output_file);
    fx25_cleanup(encoder);

    printf("Successfully created %d packet(s).\n", packet_count);
    printf("Output written to %s\n", output_filename);

    return 0;
}
