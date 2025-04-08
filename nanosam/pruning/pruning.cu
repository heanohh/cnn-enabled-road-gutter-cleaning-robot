__global__ void __kernel_conv_naive(
    float *input, float *filter, float *output,
    const int INPUT_C, const int INPUT_H,const int INPUT_W, 
    const int FILTER_H, const int FILTER_W, 
    const int PAD_H, const int PAD_W, 
    const int STRIDE_H, const int STRIDE_W, 
    const int OUTPUT_C, const int OUTPUT_H, const int OUTPUT_W
) {
 
    // Calculate the global output channel index
    int out_c = blockIdx.y * blockDim.y + threadIdx.y;
    // Calculate the global output index (height * width)
    int out_hw = blockIdx.x * blockDim.x + threadIdx.x;
    // Calculate the output height and width indices
    int out_h = out_hw / OUTPUT_W;
    int out_w = out_hw % OUTPUT_W;

    // Check if the thread is within the output channel and output bounds
    if (out_c < OUTPUT_C && out_hw < OUTPUT_H * OUTPUT_W) {

        // Initialize the output value for this thread
        float value = 0;
        // Calculate the starting position in the input feature map
        int y = STRIDE_H * out_h - PAD_H;
        int x = STRIDE_W * out_w - PAD_W;
    
        // Iterate over input channels, filter height, and filter width
        for (int c = 0; c < INPUT_C; c++) {
            for (int h = 0; h < FILTER_H; h++) {
                for (int w = 0; w < FILTER_W; w++) {
    
                    // Check if the current position is within the input feature map
                    if ((0 <= (y + h) && (y + h) < INPUT_H) && (0 <= (x + w) && (x + w) < INPUT_W)) {
                        // Accumulate the convolution value
                        value += filter[out_c * (INPUT_C * FILTER_H * FILTER_W) + c * (FILTER_H * FILTER_W) + h * (FILTER_W) + w] * input[c * (INPUT_H * INPUT_W) + (y + h) * (INPUT_W) + (x + w)];
                    }
    
                }
            }
        }
        
        // Write the computed convolution value to the output tensor
        output[out_c * (OUTPUT_H * OUTPUT_W) + out_h * (OUTPUT_W) + out_w] = value;
    }
}


__global__ void im2col(float *im, float *col, int INPUT_H, int INPUT_W, int OUTPUT_H, int OUTPUT_W, int INPUT_C, int FILTER_H, int FILTER_W, int STRIDE_H, int STRIDE_W, int PADDING_H, int PADDING_W)
{
    // Calculate the thread index
    int out = blockIdx.x * blockDim.x + threadIdx.x;

    // Ensure that the thread is within the output bounds
    if (out < OUTPUT_H * OUTPUT_W) {
        // Calculate input position based on stride and padding
        int y = STRIDE_H * (out / OUTPUT_W) - PADDING_H;
        int x = STRIDE_W * (out % OUTPUT_W) - PADDING_W;

        // Initialize index for col array (filter)
        int idx = 0;

        // Loop through input channels, filter height, and filter width
        for (int c = 0; c < INPUT_C; c++) {
            for (int h = 0; h < FILTER_H; h++) {
                for (int w = 0; w < FILTER_W; w++) {
                    // Check if the input position is within bounds
                    if ((0 <= (y + h) && (y + h) < INPUT_H) && (0 <= (x + w) && (x + w) < INPUT_W)) {
                        // Copy input value to col array
                        col[(idx * OUTPUT_W * OUTPUT_H) + out] = im[c * (INPUT_H * INPUT_W) + (y + h) * (INPUT_W) + (x + w)];
                    } else {
                        // If input position is out of bounds, set col value to 0 (padding)
                        col[(idx * OUTPUT_W * OUTPUT_H) + out] = 0;
                    }
                    idx++;
                }
            }
        }
    }
}


#define TILE_WIDTH 32
__global__ void matmul4conv(float *A, float *B, float *C, int M, int K, int N) {
    // Shared memory for tile of matrix A and matrix B
    __shared__ float Ads[TILE_WIDTH][TILE_WIDTH];
    __shared__ float Bds[TILE_WIDTH][TILE_WIDTH];

    // Thread indices
    int bx = blockIdx.x;
    int by = blockIdx.y;
    int tx = threadIdx.x;
    int ty = threadIdx.y;

    // Row and column indices of the element in matrix C to be computed
    int row = by * TILE_WIDTH + ty;
    int col = bx * TILE_WIDTH + tx;

    // Initialize the computed value to 0
    float Pvalue = 0;

    // Loop over tiles of matrix A and matrix B
    int ph;
    for (ph = 0; ph < K / TILE_WIDTH + 1; ph++) { // Loop over tiles along the shared dimension
        // Load data into shared memory for matrix A
        if (ph * TILE_WIDTH + tx < K) {
            Ads[ty][tx] = A[row * K + ph * TILE_WIDTH + tx];
        } else {
            Ads[ty][tx] = 0; // Zero-padding for out-of-bound indices
        }

        // Load data into shared memory for matrix B
        if (ph * TILE_WIDTH + ty < K) {
            Bds[ty][tx] = B[(ph * TILE_WIDTH + ty) * N + col];
        } else {
            Bds[ty][tx] = 0; // Zero-padding for out-of-bound indices
        }

        // Synchronize threads to ensure all data is loaded into shared memory
        __syncthreads();

        // Compute the dot product of the tiles
        for (int k = 0; k < TILE_WIDTH; k++) {
            Pvalue += Ads[ty][k] * Bds[k][tx];
        }

        // Synchronize threads to ensure all threads have finished computing the dot product
        __syncthreads();
    }

    // Store the computed value in matrix C if within bounds
    if (row < M && col < N) {
        C[row * N + col] = Pvalue;
    }
}


