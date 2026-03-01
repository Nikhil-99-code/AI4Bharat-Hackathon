/**
 * Circuit Breaker Pattern Implementation
 * 
 * Implements the circuit breaker pattern for external service calls
 * to prevent cascading failures and enable graceful degradation.
 * 
 * States:
 * - CLOSED: Normal operation, requests pass through
 * - OPEN: After threshold failures, requests fail fast
 * - HALF_OPEN: After timeout, test requests to check recovery
 */

export interface CircuitBreakerConfig {
  failureThreshold: number; // Number of failures before opening
  successThreshold: number; // Number of successes in HALF_OPEN before closing
  timeout: number; // Time in ms before transitioning from OPEN to HALF_OPEN
  name: string; // Circuit breaker identifier
}

export type CircuitBreakerState = 'CLOSED' | 'OPEN' | 'HALF_OPEN';

export interface CircuitBreakerMetrics {
  state: CircuitBreakerState;
  failures: number;
  successes: number;
  lastFailureTime: number;
  lastSuccessTime: number;
  totalRequests: number;
  totalFailures: number;
  totalSuccesses: number;
}

export class CircuitBreaker {
  private state: CircuitBreakerState = 'CLOSED';
  private failures: number = 0;
  private successes: number = 0;
  private lastFailureTime: number = 0;
  private lastSuccessTime: number = 0;
  private totalRequests: number = 0;
  private totalFailures: number = 0;
  private totalSuccesses: number = 0;

  constructor(private config: CircuitBreakerConfig) {}

  /**
   * Execute a function with circuit breaker protection
   */
  async execute<T>(fn: () => Promise<T>): Promise<T> {
    this.totalRequests++;

    // Check if circuit is open
    if (this.state === 'OPEN') {
      const now = Date.now();
      if (now - this.lastFailureTime > this.config.timeout) {
        console.log(`[${this.config.name}] Circuit breaker transitioning to HALF_OPEN`);
        this.state = 'HALF_OPEN';
        this.successes = 0;
      } else {
        throw new Error(`Circuit breaker is OPEN for ${this.config.name}`);
      }
    }

    try {
      const result = await fn();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }

  /**
   * Handle successful execution
   */
  private onSuccess(): void {
    this.lastSuccessTime = Date.now();
    this.totalSuccesses++;

    if (this.state === 'HALF_OPEN') {
      this.successes++;
      if (this.successes >= this.config.successThreshold) {
        console.log(`[${this.config.name}] Circuit breaker transitioning to CLOSED`);
        this.state = 'CLOSED';
        this.failures = 0;
        this.successes = 0;
      }
    } else if (this.state === 'CLOSED') {
      this.failures = 0; // Reset failure count on success
    }
  }

  /**
   * Handle failed execution
   */
  private onFailure(): void {
    this.lastFailureTime = Date.now();
    this.failures++;
    this.totalFailures++;

    if (this.state === 'HALF_OPEN') {
      console.log(`[${this.config.name}] Circuit breaker transitioning to OPEN (failure in HALF_OPEN)`);
      this.state = 'OPEN';
      this.successes = 0;
    } else if (this.state === 'CLOSED' && this.failures >= this.config.failureThreshold) {
      console.log(`[${this.config.name}] Circuit breaker transitioning to OPEN (threshold reached)`);
      this.state = 'OPEN';
    }
  }

  /**
   * Get current circuit breaker metrics
   */
  getMetrics(): CircuitBreakerMetrics {
    return {
      state: this.state,
      failures: this.failures,
      successes: this.successes,
      lastFailureTime: this.lastFailureTime,
      lastSuccessTime: this.lastSuccessTime,
      totalRequests: this.totalRequests,
      totalFailures: this.totalFailures,
      totalSuccesses: this.totalSuccesses,
    };
  }

  /**
   * Get current state
   */
  getState(): CircuitBreakerState {
    return this.state;
  }

  /**
   * Manually reset the circuit breaker
   */
  reset(): void {
    console.log(`[${this.config.name}] Circuit breaker manually reset`);
    this.state = 'CLOSED';
    this.failures = 0;
    this.successes = 0;
  }

  /**
   * Check if circuit breaker is allowing requests
   */
  isAllowingRequests(): boolean {
    if (this.state === 'OPEN') {
      const now = Date.now();
      if (now - this.lastFailureTime > this.config.timeout) {
        return true; // Will transition to HALF_OPEN on next request
      }
      return false;
    }
    return true;
  }
}

/**
 * Create a circuit breaker with default configuration
 */
export function createCircuitBreaker(name: string, overrides?: Partial<CircuitBreakerConfig>): CircuitBreaker {
  const defaultConfig: CircuitBreakerConfig = {
    failureThreshold: 3,
    successThreshold: 2,
    timeout: 60000, // 1 minute
    name,
  };

  return new CircuitBreaker({ ...defaultConfig, ...overrides });
}
