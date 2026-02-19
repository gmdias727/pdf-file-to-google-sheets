import type { Actions } from './$types';

export const actions = {
    parse: async ({ request, fetch }) => {
        const formData = await request.formData();
        const files = formData.getAll('pdf') as File[];

        if (!files.length || files.every((f) => f.size === 0)) {
            return { success: false, error: 'Nenhum arquivo selecionado.' };
        }

        const invalidFiles = files.filter((f) => !f.name.toLowerCase().endsWith('.pdf'));
        if (invalidFiles.length > 0) {
            return {
                success: false,
                error: `Apenas arquivos PDF são aceitos. Arquivos inválidos: ${invalidFiles.map((f) => f.name).join(', ')}`,
            };
        }

        try {
            // Parse each file in parallel
            const results = await Promise.all(
                files.map(async (file) => {
                    const backendForm = new FormData();
                    backendForm.append('file', file);

                    const response = await fetch('http://localhost:8000/api/parse', {
                        method: 'POST',
                        body: backendForm,
                    });

                    if (!response.ok) {
                        const errorData = await response
                            .json()
                            .catch(() => ({ detail: 'Erro desconhecido' }));
                        return {
                            success: false as const,
                            fileName: file.name,
                            error: errorData.detail || `Erro do servidor: ${response.status}`,
                        };
                    }

                    const data = await response.json();
                    return {
                        success: true as const,
                        fileName: file.name,
                        bank: data.bank as string,
                        transactions: data.transactions as Array<Record<string, unknown>>,
                        totalTransactions: data.total_transactions as number,
                    };
                })
            );

            const successful = results.filter((r) => r.success);
            const failed = results.filter((r) => !r.success);

            if (successful.length === 0) {
                return {
                    success: false,
                    error: failed
                        .map((r) => `${r.fileName}: ${'error' in r ? r.error : 'Erro desconhecido'}`)
                        .join('; '),
                };
            }

            // Merge all transactions
            const allTransactions = successful.flatMap((r) =>
                r.success ? r.transactions : []
            );
            const banks = [...new Set(successful.map((r) => (r.success ? r.bank : '')))].filter(
                Boolean
            );

            return {
                success: true,
                banks,
                transactions: allTransactions,
                totalTransactions: allTransactions.length,
                fileNames: successful.map((r) => r.fileName),
                errors: failed.length
                    ? failed.map((r) => `${r.fileName}: ${'error' in r ? r.error : 'Erro'}`)
                    : null,
            };
        } catch (err) {
            return {
                success: false,
                error: 'Não foi possível conectar ao servidor de processamento. Verifique se o backend está rodando na porta 8000.',
            };
        }
    },
} satisfies Actions;
