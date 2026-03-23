import { NextRequest, NextResponse } from 'next/server';

// 在Next.js API路由中，优先使用METADATA_SERVICE_URL（服务器端环境变量）
// 如果运行在Docker容器内，使用服务名 metadata-service:8005
// 如果运行在本地开发环境，使用 localhost:8005
// 注意：在服务器端（Next.js API路由），window是undefined，所以这里总是服务器端
// 检测是否在Docker容器内运行：在Linux平台上，如果METADATA_SERVICE_URL未设置，默认使用Docker服务名
const METADATA_SERVICE_URL =
  process.env.METADATA_SERVICE_URL ||
  (process.platform === 'linux' ? 'http://metadata-service:8005' : 'http://localhost:8005');

// 调试：输出配置的URL（仅在开发环境）
if (process.env.NODE_ENV === 'development') {
  console.log('METADATA_SERVICE_URL:', METADATA_SERVICE_URL);
}

// 获取所有类型的元数据汇总
export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const type = searchParams.get('type'); // data-assets, workflows, ai-models, business-entities
    const limit = searchParams.get('limit') || '100';
    const skip = searchParams.get('skip') || searchParams.get('offset') || '0'; // 支持skip和offset两种参数
    const search = searchParams.get('search');

    // 根据类型调用不同的API
    // 注意：metadata-service的API路径是 /api/ 而不是 /api/v1/，使用 skip 和 limit 参数
    let url = '';
    if (type === 'data-assets') {
      const classification = searchParams.get('classification');
      // 如果limit很大（>1000），使用分页获取所有数据
      const requestLimit = parseInt(limit);
      if (requestLimit > 1000) {
        // 分页获取所有数据
        const fetchAllWithPagination = async (endpoint: string) => {
          const allItems: any[] = [];
          let currentSkip = 0;
          const pageLimit = 1000; // 每次获取1000条
          let hasMore = true;

          while (hasMore) {
            const pageUrl = `${METADATA_SERVICE_URL}${endpoint}?skip=${currentSkip}&limit=${pageLimit}${search ? `&search=${search}` : ''}${classification ? `&classification=${classification}` : ''}`;
            try {
              const response = await fetch(`${pageUrl}&include_total=true`, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' },
                cache: 'no-store',
              });

              if (!response.ok) {
                console.error(`Failed to fetch page: ${response.status}`);
                break;
              }

              const items = await response.json();
              // 获取总数（只在第一页时获取）
              if (currentSkip === 0) {
                const totalCountHeader = response.headers.get('X-Total-Count');
                if (totalCountHeader) {
                  // 将总数存储在allItems的元数据中
                  (allItems as any).__total = parseInt(totalCountHeader);
                }
              }
              if (!Array.isArray(items) || items.length === 0) {
                hasMore = false;
              } else {
                allItems.push(...items);
                currentSkip += pageLimit;
                // 如果返回的数据少于pageLimit，说明已经获取了所有数据
                if (items.length < pageLimit) {
                  hasMore = false;
                }
              }
            } catch (error) {
              console.error(`Error fetching page:`, error);
              break;
            }
          }

          return allItems;
        };

        const allItems = await fetchAllWithPagination('/api/data-assets');
        const total = (allItems as any).__total || allItems.length;
        // 移除元数据
        const cleanItems = allItems.filter((item: any) => !item.__total);
        return NextResponse.json({
          items: cleanItems,
          total: total,
        });
      }
      // 如果limit <= 1000，使用普通请求（包含总数）
      const searchParam = search ? `&search=${encodeURIComponent(search)}` : '';
      const classificationParam = classification
        ? `&classification=${encodeURIComponent(classification)}`
        : '';
      url = `${METADATA_SERVICE_URL}/api/data-assets?skip=${skip}&limit=${limit}${searchParam}${classificationParam}&include_total=true`;

      // 调试日志
      if (process.env.NODE_ENV === 'development') {
        console.log('Fetching data assets from:', url);
      }
    } else if (type === 'workflows') {
      const classification = searchParams.get('classification');
      const requestLimit = parseInt(limit);
      if (requestLimit > 1000) {
        const fetchAllWithPagination = async (endpoint: string) => {
          const allItems: any[] = [];
          let currentSkip = 0;
          const pageLimit = 1000;
          let hasMore = true;

          while (hasMore) {
            const pageUrl = `${METADATA_SERVICE_URL}${endpoint}?skip=${currentSkip}&limit=${pageLimit}${search ? `&search=${search}` : ''}${classification ? `&classification=${classification}` : ''}`;
            try {
              const response = await fetch(pageUrl, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' },
                cache: 'no-store',
              });

              if (!response.ok) break;

              const items = await response.json();
              if (!Array.isArray(items) || items.length === 0) {
                hasMore = false;
              } else {
                allItems.push(...items);
                currentSkip += pageLimit;
                if (items.length < pageLimit) hasMore = false;
              }
            } catch (error) {
              console.error(`Error fetching page:`, error);
              break;
            }
          }
          return allItems;
        };

        const allItems = await fetchAllWithPagination('/api/workflows');
        return NextResponse.json({ items: allItems, total: allItems.length });
      }
      const classificationParam = classification
        ? `&classification=${encodeURIComponent(classification)}`
        : '';
      url = `${METADATA_SERVICE_URL}/api/workflows?skip=${skip}&limit=${limit}${search ? `&search=${encodeURIComponent(search)}` : ''}${classificationParam}`;
    } else if (type === 'ai-models') {
      const classification = searchParams.get('classification');
      const requestLimit = parseInt(limit);
      if (requestLimit > 1000) {
        const fetchAllWithPagination = async (endpoint: string) => {
          const allItems: any[] = [];
          let currentSkip = 0;
          const pageLimit = 1000;
          let hasMore = true;

          while (hasMore) {
            const pageUrl = `${METADATA_SERVICE_URL}${endpoint}?skip=${currentSkip}&limit=${pageLimit}${search ? `&search=${search}` : ''}${classification ? `&classification=${classification}` : ''}`;
            try {
              const response = await fetch(pageUrl, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' },
                cache: 'no-store',
              });

              if (!response.ok) break;

              const items = await response.json();
              if (!Array.isArray(items) || items.length === 0) {
                hasMore = false;
              } else {
                allItems.push(...items);
                currentSkip += pageLimit;
                if (items.length < pageLimit) hasMore = false;
              }
            } catch (error) {
              console.error(`Error fetching page:`, error);
              break;
            }
          }
          return allItems;
        };

        const allItems = await fetchAllWithPagination('/api/ai-models');
        return NextResponse.json({ items: allItems, total: allItems.length });
      }
      const classificationParam = classification
        ? `&classification=${encodeURIComponent(classification)}`
        : '';
      url = `${METADATA_SERVICE_URL}/api/ai-models?skip=${skip}&limit=${limit}${search ? `&search=${encodeURIComponent(search)}` : ''}${classificationParam}`;
    } else if (type === 'business-entities') {
      const classification = searchParams.get('classification');
      const requestLimit = parseInt(limit);
      if (requestLimit > 1000) {
        const fetchAllWithPagination = async (endpoint: string) => {
          const allItems: any[] = [];
          let currentSkip = 0;
          const pageLimit = 1000;
          let hasMore = true;

          while (hasMore) {
            const pageUrl = `${METADATA_SERVICE_URL}${endpoint}?skip=${currentSkip}&limit=${pageLimit}${search ? `&search=${search}` : ''}${classification ? `&classification=${classification}` : ''}`;
            try {
              const response = await fetch(pageUrl, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' },
                cache: 'no-store',
              });

              if (!response.ok) break;

              const items = await response.json();
              if (!Array.isArray(items) || items.length === 0) {
                hasMore = false;
              } else {
                allItems.push(...items);
                currentSkip += pageLimit;
                if (items.length < pageLimit) hasMore = false;
              }
            } catch (error) {
              console.error(`Error fetching page:`, error);
              break;
            }
          }
          return allItems;
        };

        const allItems = await fetchAllWithPagination('/api/business-entities');
        return NextResponse.json({ items: allItems, total: allItems.length });
      }
      const classificationParam = classification
        ? `&classification=${encodeURIComponent(classification)}`
        : '';
      url = `${METADATA_SERVICE_URL}/api/business-entities?skip=${skip}&limit=${limit}${search ? `&search=${encodeURIComponent(search)}` : ''}${classificationParam}`;
    } else {
      // 获取所有类型的汇总
      // 先获取总数（使用大limit），然后获取最近的数据
      const fetchWithErrorHandling = async (url: string) => {
        try {
          const controller = new AbortController();
          const timeoutId = setTimeout(() => controller.abort(), 10000); // 10秒超时

          console.log(`Fetching metadata from: ${url}`);

          const response = await fetch(url, {
            method: 'GET',
            headers: {
              'Content-Type': 'application/json',
            },
            cache: 'no-store',
            signal: controller.signal,
          });

          clearTimeout(timeoutId);

          if (!response.ok) {
            console.error(`Failed to fetch ${url}: ${response.status} ${response.statusText}`);
            const errorText = await response.text();
            console.error(`Error response: ${errorText}`);
            return [];
          }

          const data = await response.json();
          console.log(
            `Successfully fetched ${url}: ${Array.isArray(data) ? data.length : 'not array'} items`
          );
          return Array.isArray(data) ? data : [];
        } catch (error: any) {
          if (error.name === 'AbortError') {
            console.error(`Timeout fetching ${url}`);
          } else {
            console.error(`Error fetching ${url}:`, error.message || error);
          }
          return [];
        }
      };

      // 获取所有数据以计算总数（metadata-service的limit最大为100，需要分页获取）
      const fetchAllWithPagination = async (endpoint: string, maxItems?: number) => {
        const allItems: any[] = [];
        let skip = 0;
        const limit = 100; // metadata-service的limit最大为100
        let hasMore = true;

        while (hasMore) {
          const items = await fetchWithErrorHandling(
            `${METADATA_SERVICE_URL}${endpoint}?skip=${skip}&limit=${limit}`
          );
          if (items.length === 0) {
            hasMore = false;
          } else {
            allItems.push(...items);
            skip += limit;
            // 如果返回的数据少于limit，说明已经获取了所有数据
            if (items.length < limit) {
              hasMore = false;
            }
            // 如果指定了maxItems，检查是否达到限制
            if (maxItems && allItems.length >= maxItems) {
              hasMore = false;
            }
          }
        }
        return allItems;
      };

      const [
        dataAssetsAll,
        workflowsAll,
        aiModelsAll,
        businessEntitiesAll,
        dataAssetsRecent,
        workflowsRecent,
        aiModelsRecent,
        businessEntitiesRecent,
      ] = await Promise.all([
        // 获取所有数据以计算总数（使用分页）
        fetchAllWithPagination('/api/data-assets'),
        fetchAllWithPagination('/api/workflows'),
        fetchAllWithPagination('/api/ai-models'),
        fetchAllWithPagination('/api/business-entities'),
        // 获取最近的数据用于显示
        fetchWithErrorHandling(`${METADATA_SERVICE_URL}/api/data-assets?skip=0&limit=10`),
        fetchWithErrorHandling(`${METADATA_SERVICE_URL}/api/workflows?skip=0&limit=10`),
        fetchWithErrorHandling(`${METADATA_SERVICE_URL}/api/ai-models?skip=0&limit=10`),
        fetchWithErrorHandling(`${METADATA_SERVICE_URL}/api/business-entities?skip=0&limit=10`),
      ]);

      console.log('Metadata summary:', {
        data_assets: dataAssetsAll.length,
        workflows: workflowsAll.length,
        ai_models: aiModelsAll.length,
        business_entities: businessEntitiesAll.length,
        service_url: METADATA_SERVICE_URL,
      });

      return NextResponse.json({
        summary: {
          data_assets: dataAssetsAll.length,
          workflows: workflowsAll.length,
          ai_models: aiModelsAll.length,
          business_entities: businessEntitiesAll.length,
        },
        recent: {
          data_assets: dataAssetsRecent.slice(0, 10), // 增加到10条，与limit一致
          workflows: workflowsRecent.slice(0, 10),
          ai_models: aiModelsRecent.slice(0, 10),
          business_entities: businessEntitiesRecent.slice(0, 10),
        },
      });
    }

    if (!url) {
      return NextResponse.json({ error: 'Invalid type' }, { status: 400 });
    }

    // 调试日志
    if (process.env.NODE_ENV === 'development') {
      console.log('Fetching from metadata-service:', url);
    }

    let response: Response;
    try {
      response = await fetch(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        cache: 'no-store',
      });
    } catch (fetchError) {
      console.error('Fetch error:', fetchError);
      throw new Error(
        `Failed to connect to metadata-service at ${url}: ${fetchError instanceof Error ? fetchError.message : 'Unknown error'}`
      );
    }

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`Metadata service error [${url}]: ${response.status} - ${errorText}`);
      // 如果返回404，可能是URL配置问题
      if (response.status === 404) {
        console.error(`URL not found: ${url}, METADATA_SERVICE_URL: ${METADATA_SERVICE_URL}`);
      }
      throw new Error(`Metadata service error: ${response.status} - ${errorText}`);
    }

    // 对于数据资产，尝试从响应头获取总数
    let total = 0;
    const totalCountHeader =
      response.headers.get('X-Total-Count') || response.headers.get('x-total-count');
    if (totalCountHeader) {
      total = parseInt(totalCountHeader);
    }

    const data = await response.json();
    const items = Array.isArray(data) ? data : [];

    // 调试日志
    console.log(`API route [${type}]:`, {
      url,
      dataType: Array.isArray(data) ? 'array' : typeof data,
      itemsCount: items.length,
      totalFromHeader: total,
      skip,
      limit,
      firstItem: items.length > 0 ? items[0] : null,
    });

    // 如果没有从响应头获取到总数，进行估算
    if (type === 'data-assets' && total === 0) {
      if (items.length === parseInt(limit)) {
        // 返回的数据量等于limit，可能还有更多数据
        total = parseInt(skip) + items.length + parseInt(limit);
      } else {
        // 如果没有更多数据，使用实际数量
        total = parseInt(skip) + items.length;
      }
    } else if (total === 0) {
      total = items.length;
    }

    // 创建响应并添加总数头
    const nextResponse = NextResponse.json({
      items: items,
      total: total,
      page: Math.floor(parseInt(skip) / parseInt(limit)) + 1,
      pageSize: parseInt(limit),
      hasMore: items.length === parseInt(limit),
    });

    // 如果有总数头，也传递给前端
    if (totalCountHeader) {
      nextResponse.headers.set('X-Total-Count', totalCountHeader);
    }

    return nextResponse;
  } catch (error) {
    console.error('Failed to fetch metadata:', error);
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    const errorStack = error instanceof Error ? error.stack : undefined;

    // 在开发环境输出更详细的错误信息
    if (process.env.NODE_ENV === 'development') {
      console.error('Error details:', {
        message: errorMessage,
        stack: errorStack,
        METADATA_SERVICE_URL,
      });
    }

    return NextResponse.json(
      {
        items: [],
        total: 0,
        error: errorMessage,
        ...(process.env.NODE_ENV === 'development' && {
          details: errorStack,
          serviceUrl: METADATA_SERVICE_URL,
        }),
      },
      { status: 500 }
    );
  }
}
