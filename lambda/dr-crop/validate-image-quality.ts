/**
 * Lambda Function: Validate Image Quality
 * 
 * This function validates crop image quality before analysis.
 * It checks resolution, format, file size, blur, lighting, and focus issues.
 * 
 * Requirements: 1.3
 */

import { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda';
import sharp from 'sharp';

interface ValidateImageRequest {
  imageData: string; // Base64 encoded image
  imageFormat: 'png' | 'jpeg' | 'gif' | 'webp';
  language?: 'en' | 'bn' | 'hi';
}

interface ImageQualityResult {
  valid: boolean;
  issues: ImageIssue[];
  recommendations: string[];
  metadata: ImageMetadata;
}

interface ImageIssue {
  type: 'resolution' | 'format' | 'size' | 'blur' | 'lighting' | 'focus';
  severity: 'error' | 'warning';
  message: string;
}

interface ImageMetadata {
  width: number;
  height: number;
  format: string;
  size: number;
  aspectRatio: number;
  estimatedBlur?: number;
  estimatedBrightness?: number;
}

// Multilingual guidance messages
const GUIDANCE_MESSAGES = {
  en: {
    resolution_low: 'Image resolution is too low. Please take a photo with at least 800x600 pixels.',
    resolution_warning: 'Image resolution is acceptable but could be better. Try to use a higher resolution camera.',
    size_too_large: 'Image file size is too large (max 10MB). Please compress the image or reduce quality.',
    size_too_small: 'Image file size is too small. This may indicate poor quality. Please take a clearer photo.',
    format_unsupported: 'Image format is not supported. Please use JPEG, PNG, WEBP, or GIF format.',
    blur_detected: 'Image appears blurry. Please hold the camera steady and ensure the crop is in focus.',
    lighting_poor: 'Image has poor lighting. Please take the photo in good natural light or use flash.',
    lighting_overexposed: 'Image is overexposed (too bright). Please reduce lighting or move to shade.',
    lighting_underexposed: 'Image is underexposed (too dark). Please increase lighting or use flash.',
    distance_too_close: 'Camera appears too close. Please step back to capture the entire affected area.',
    distance_too_far: 'Camera appears too far. Please move closer to show clear details of the crop issue.',
    general_improvement: 'For best results: Use good lighting, hold camera steady, focus on affected area, and capture from 1-2 feet distance.',
  },
  bn: {
    resolution_low: 'ছবির রেজোলিউশন খুব কম। অনুগ্রহ করে কমপক্ষে ৮০০x৬০০ পিক্সেলের একটি ছবি তুলুন।',
    resolution_warning: 'ছবির রেজোলিউশন গ্রহণযোগ্য কিন্তু আরও ভাল হতে পারে। উচ্চ রেজোলিউশন ক্যামেরা ব্যবহার করার চেষ্টা করুন।',
    size_too_large: 'ছবির ফাইল সাইজ খুব বড় (সর্বোচ্চ ১০এমবি)। অনুগ্রহ করে ছবি কম্প্রেস করুন বা গুণমান কমান।',
    size_too_small: 'ছবির ফাইল সাইজ খুব ছোট। এটি খারাপ গুণমান নির্দেশ করতে পারে। অনুগ্রহ করে একটি পরিষ্কার ছবি তুলুন।',
    format_unsupported: 'ছবির ফরম্যাট সমর্থিত নয়। অনুগ্রহ করে JPEG, PNG, WEBP, বা GIF ফরম্যাট ব্যবহার করুন।',
    blur_detected: 'ছবি ঝাপসা দেখাচ্ছে। অনুগ্রহ করে ক্যামেরা স্থির রাখুন এবং ফসল ফোকাসে আছে তা নিশ্চিত করুন।',
    lighting_poor: 'ছবিতে আলো খারাপ। অনুগ্রহ করে ভাল প্রাকৃতিক আলোতে ছবি তুলুন বা ফ্ল্যাশ ব্যবহার করুন।',
    lighting_overexposed: 'ছবি অতিরিক্ত উজ্জ্বল। অনুগ্রহ করে আলো কমান বা ছায়ায় যান।',
    lighting_underexposed: 'ছবি খুব অন্ধকার। অনুগ্রহ করে আলো বাড়ান বা ফ্ল্যাশ ব্যবহার করুন।',
    distance_too_close: 'ক্যামেরা খুব কাছে মনে হচ্ছে। সম্পূর্ণ প্রভাবিত এলাকা ক্যাপচার করতে পিছনে সরে যান।',
    distance_too_far: 'ক্যামেরা খুব দূরে মনে হচ্ছে। ফসলের সমস্যার স্পষ্ট বিবরণ দেখাতে কাছে যান।',
    general_improvement: 'সর্বোত্তম ফলাফলের জন্য: ভাল আলো ব্যবহার করুন, ক্যামেরা স্থির রাখুন, প্রভাবিত এলাকায় ফোকাস করুন, এবং ১-২ ফুট দূরত্ব থেকে ক্যাপচার করুন।',
  },
  hi: {
    resolution_low: 'छवि रिज़ॉल्यूशन बहुत कम है। कृपया कम से कम 800x600 पिक्सेल की फोटो लें।',
    resolution_warning: 'छवि रिज़ॉल्यूशन स्वीकार्य है लेकिन बेहतर हो सकता है। उच्च रिज़ॉल्यूशन कैमरा उपयोग करने का प्रयास करें।',
    size_too_large: 'छवि फ़ाइल का आकार बहुत बड़ा है (अधिकतम 10MB)। कृपया छवि को संपीड़ित करें या गुणवत्ता कम करें।',
    size_too_small: 'छवि फ़ाइल का आकार बहुत छोटा है। यह खराब गुणवत्ता का संकेत हो सकता है। कृपया एक स्पष्ट फोटो लें।',
    format_unsupported: 'छवि प्रारूप समर्थित नहीं है। कृपया JPEG, PNG, WEBP, या GIF प्रारूप का उपयोग करें।',
    blur_detected: 'छवि धुंधली दिखाई दे रही है। कृपया कैमरा स्थिर रखें और सुनिश्चित करें कि फसल फोकस में है।',
    lighting_poor: 'छवि में खराब प्रकाश है। कृपया अच्छी प्राकृतिक रोशनी में फोटो लें या फ्लैश का उपयोग करें।',
    lighting_overexposed: 'छवि अधिक उजागर है (बहुत उज्ज्वल)। कृपया प्रकाश कम करें या छाया में जाएं।',
    lighting_underexposed: 'छवि कम उजागर है (बहुत अंधेरा)। कृपया प्रकाश बढ़ाएं या फ्लैश का उपयोग करें।',
    distance_too_close: 'कैमरा बहुत करीब लगता है। पूरे प्रभावित क्षेत्र को कैप्चर करने के लिए पीछे हटें।',
    distance_too_far: 'कैमरा बहुत दूर लगता है। फसल की समस्या का स्पष्ट विवरण दिखाने के लिए करीब जाएं।',
    general_improvement: 'सर्वोत्तम परिणामों के लिए: अच्छी रोशनी का उपयोग करें, कैमरा स्थिर रखें, प्रभावित क्षेत्र पर ध्यान केंद्रित करें, और 1-2 फीट की दूरी से कैप्चर करें।',
  },
};

/**
 * Estimate image blur using Laplacian variance
 */
async function estimateBlur(imageBuffer: Buffer): Promise<number> {
  try {
    // Convert to grayscale and get raw pixel data
    const { data, info } = await sharp(imageBuffer)
      .grayscale()
      .raw()
      .toBuffer({ resolveWithObject: true });

    // Calculate Laplacian variance (simplified)
    let variance = 0;
    const width = info.width;
    const height = info.height;

    // Sample pixels (not all for performance)
    const sampleRate = 10;
    let count = 0;

    for (let y = 1; y < height - 1; y += sampleRate) {
      for (let x = 1; x < width - 1; x += sampleRate) {
        const idx = y * width + x;
        const center = data[idx];
        const top = data[(y - 1) * width + x];
        const bottom = data[(y + 1) * width + x];
        const left = data[y * width + (x - 1)];
        const right = data[y * width + (x + 1)];

        const laplacian = Math.abs(4 * center - top - bottom - left - right);
        variance += laplacian * laplacian;
        count++;
      }
    }

    return variance / count;
  } catch (error) {
    console.error('Error estimating blur:', error);
    return 0;
  }
}

/**
 * Estimate image brightness
 */
async function estimateBrightness(imageBuffer: Buffer): Promise<number> {
  try {
    const { data, info } = await sharp(imageBuffer)
      .grayscale()
      .raw()
      .toBuffer({ resolveWithObject: true });

    // Calculate average brightness
    let sum = 0;
    for (let i = 0; i < data.length; i++) {
      sum += data[i];
    }

    return sum / data.length / 255; // Normalize to 0-1
  } catch (error) {
    console.error('Error estimating brightness:', error);
    return 0.5;
  }
}

/**
 * Validate image quality
 */
async function validateImage(
  imageBuffer: Buffer,
  format: string,
  language: 'en' | 'bn' | 'hi'
): Promise<ImageQualityResult> {
  const issues: ImageIssue[] = [];
  const recommendations: string[] = [];
  const messages = GUIDANCE_MESSAGES[language];

  // Get image metadata
  const metadata = await sharp(imageBuffer).metadata();
  const width = metadata.width || 0;
  const height = metadata.height || 0;
  const size = imageBuffer.length;
  const aspectRatio = width / height;

  // Check file size
  const maxSize = 10 * 1024 * 1024; // 10MB
  const minSize = 10 * 1024; // 10KB

  if (size > maxSize) {
    issues.push({
      type: 'size',
      severity: 'error',
      message: messages.size_too_large,
    });
  } else if (size < minSize) {
    issues.push({
      type: 'size',
      severity: 'warning',
      message: messages.size_too_small,
    });
  }

  // Check resolution
  const minWidth = 800;
  const minHeight = 600;
  const recommendedWidth = 1920;
  const recommendedHeight = 1080;

  if (width < minWidth || height < minHeight) {
    issues.push({
      type: 'resolution',
      severity: 'error',
      message: messages.resolution_low,
    });
  } else if (width < recommendedWidth || height < recommendedHeight) {
    issues.push({
      type: 'resolution',
      severity: 'warning',
      message: messages.resolution_warning,
    });
  }

  // Check format
  const supportedFormats = ['jpeg', 'jpg', 'png', 'webp', 'gif'];
  if (!supportedFormats.includes(format.toLowerCase())) {
    issues.push({
      type: 'format',
      severity: 'error',
      message: messages.format_unsupported,
    });
  }

  // Estimate blur
  const blurScore = await estimateBlur(imageBuffer);
  const blurThreshold = 100; // Adjust based on testing

  if (blurScore < blurThreshold) {
    issues.push({
      type: 'blur',
      severity: 'warning',
      message: messages.blur_detected,
    });
    recommendations.push(messages.blur_detected);
  }

  // Estimate brightness
  const brightness = await estimateBrightness(imageBuffer);

  if (brightness < 0.2) {
    issues.push({
      type: 'lighting',
      severity: 'warning',
      message: messages.lighting_underexposed,
    });
    recommendations.push(messages.lighting_underexposed);
  } else if (brightness > 0.8) {
    issues.push({
      type: 'lighting',
      severity: 'warning',
      message: messages.lighting_overexposed,
    });
    recommendations.push(messages.lighting_overexposed);
  }

  // Check aspect ratio (extreme ratios might indicate cropping issues)
  if (aspectRatio < 0.5 || aspectRatio > 2.0) {
    recommendations.push(messages.distance_too_close);
  }

  // Add general improvement guidance if there are issues
  if (issues.length > 0) {
    recommendations.push(messages.general_improvement);
  }

  // Determine if image is valid (no error-level issues)
  const valid = !issues.some(issue => issue.severity === 'error');

  return {
    valid,
    issues,
    recommendations: [...new Set(recommendations)], // Remove duplicates
    metadata: {
      width,
      height,
      format: metadata.format || format,
      size,
      aspectRatio,
      estimatedBlur: blurScore,
      estimatedBrightness: brightness,
    },
  };
}

/**
 * Main Lambda handler
 */
export async function handler(event: APIGatewayProxyEvent): Promise<APIGatewayProxyResult> {
  console.log('Received image quality validation request');

  try {
    // Parse request body
    const request: ValidateImageRequest = JSON.parse(event.body || '{}');

    // Validate required fields
    if (!request.imageData || !request.imageFormat) {
      return {
        statusCode: 400,
        body: JSON.stringify({
          error: 'Missing required fields: imageData, imageFormat',
        }),
      };
    }

    // Decode base64 image
    const imageBuffer = Buffer.from(request.imageData, 'base64');
    const language = request.language || 'en';

    // Validate image quality
    console.log('Validating image quality...');
    const result = await validateImage(imageBuffer, request.imageFormat, language);
    console.log(`Validation complete. Valid: ${result.valid}, Issues: ${result.issues.length}`);

    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
      },
      body: JSON.stringify(result),
    };
  } catch (error) {
    console.error('Error validating image quality:', error);

    return {
      statusCode: 500,
      body: JSON.stringify({
        error: 'Internal server error',
        message: error instanceof Error ? error.message : 'Unknown error occurred',
      }),
    };
  }
}
