<script lang="ts">
	import { enhance } from "$app/forms";

	interface Transaction {
		date: string;
		description: string;
		amount: number;
		transaction_type: string;
		operation_type: string;
		bank: string;
	}

	let { form } = $props();

	let loading = $state(false);
	let dragOver = $state(false);
	let selectedFiles = $state<File[]>([]);
	let copied = $state(false);
	let fileInput = $state<HTMLInputElement | null>(null);

	let transactions = $derived<Transaction[]>(form?.transactions ?? []);
	let banks = $derived<string[]>(form?.banks ?? []);
	let error = $derived<string>(form?.error ?? "");
	let partialErrors = $derived<string[] | null>(form?.errors ?? null);
	let hasResults = $derived(
		form?.success === true && transactions.length > 0,
	);

	function handleDragOver(e: DragEvent) {
		e.preventDefault();
		dragOver = true;
	}

	function handleDragLeave() {
		dragOver = false;
	}

	function handleDrop(e: DragEvent) {
		e.preventDefault();
		dragOver = false;
		const files = e.dataTransfer?.files;
		if (files) {
			const pdfFiles = Array.from(files).filter((f) =>
				f.name.toLowerCase().endsWith(".pdf"),
			);
			if (pdfFiles.length && fileInput) {
				const dt = new DataTransfer();
				pdfFiles.forEach((f) => dt.items.add(f));
				fileInput.files = dt.files;
				selectedFiles = pdfFiles;
			}
		}
	}

	function handleFileChange(e: Event) {
		const target = e.target as HTMLInputElement;
		if (target.files) {
			selectedFiles = Array.from(target.files);
		}
	}

	function removeFile(index: number) {
		const newFiles = selectedFiles.filter((_, i) => i !== index);
		selectedFiles = newFiles;
		if (fileInput) {
			const dt = new DataTransfer();
			newFiles.forEach((f) => dt.items.add(f));
			fileInput.files = dt.files;
		}
	}

	function formatCurrency(value: number): string {
		const abs = Math.abs(value);
		const formatted = abs.toLocaleString("pt-BR", {
			minimumFractionDigits: 2,
			maximumFractionDigits: 2,
		});
		return value < 0 ? `-R$ ${formatted}` : `R$ ${formatted}`;
	}

	function bankLabel(b: string): string {
		const labels: Record<string, string> = {
			itau: "Itaú",
			nubank: "Nubank",
			inter: "Banco Inter",
		};
		return labels[b] || b;
	}

	function copyToClipboard() {
		if (!transactions.length) return;
		const header = "Data\tDescrição\tValor\tTipo\tOperação\tBanco";
		const rows = transactions.map(
			(t) =>
				`${t.date}\t${t.description}\t${t.amount}\t${t.transaction_type}\t${t.operation_type}\t${t.bank}`,
		);
		navigator.clipboard.writeText([header, ...rows].join("\n")).then(() => {
			copied = true;
			setTimeout(() => (copied = false), 2000);
		});
	}

	function exportCSV() {
		if (!transactions.length) return;
		const header = "Data,Descrição,Valor,Tipo,Operação,Banco";
		const rows = transactions.map(
			(t) =>
				`${t.date},"${t.description.replace(/"/g, '""')}",${t.amount},${t.transaction_type},${t.operation_type},${t.bank}`,
		);
		const csv = [header, ...rows].join("\n");
		const blob = new Blob(["\ufeff" + csv], {
			type: "text/csv;charset=utf-8;",
		});
		const url = URL.createObjectURL(blob);
		const a = document.createElement("a");
		a.href = url;
		a.download = `extrato_${banks.join("_") || "banco"}_${new Date().toISOString().slice(0, 10)}.csv`;
		a.click();
		URL.revokeObjectURL(url);
	}

	let totalDeposits = $derived(
		transactions
			.filter((t) => t.operation_type === "deposit")
			.reduce((s, t) => s + t.amount, 0),
	);
	let totalWithdrawals = $derived(
		transactions
			.filter((t) => t.operation_type === "withdrawal")
			.reduce((s, t) => s + Math.abs(t.amount), 0),
	);
	let formatBytes = (bytes: number) => {
		if (bytes < 1024) return `${bytes} B`;
		return `${(bytes / 1024).toFixed(0)} KB`;
	};

	let currentPage = $state(1);
	let itemsPerPage = $state(10);
	let totalPages = $derived(Math.ceil(transactions.length / itemsPerPage) || 1);
	
	$effect(() => {
		if (currentPage > totalPages) currentPage = totalPages;
		if (currentPage < 1) currentPage = 1;
	});

	let paginatedTransactions = $derived(
		transactions.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage)
	);
</script>

<!-- ─── Header ─── -->
<header class="header">
	<div class="container">
		<div class="header-content">
			<div class="logo">
				<svg
					width="24"
					height="24"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					stroke-width="1.5"
				>
					<path
						d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"
					/>
					<polyline points="14 2 14 8 20 8" />
					<line x1="16" y1="13" x2="8" y2="13" />
					<line x1="16" y1="17" x2="8" y2="17" />
					<polyline points="10 9 9 9 8 9" />
				</svg>
				<div>
					<h1>Extrato PDF Parser</h1>
					<p class="tagline">Extraia dados de extratos bancários</p>
				</div>
			</div>
			<a
				href="https://github.com"
				target="_blank"
				rel="noopener noreferrer"
				class="github-link"
			>
				<svg
					width="18"
					height="18"
					viewBox="0 0 24 24"
					fill="currentColor"
				>
					<path
						d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"
					/>
				</svg>
				Open Source
			</a>
		</div>
	</div>
</header>

<!-- ─── Main Content ─── -->
<main class="main container">
	<!-- Upload Section -->
	<section class="upload-section">
		<form
			method="POST"
			action="?/parse"
			enctype="multipart/form-data"
			use:enhance={() => {
				loading = true;
				return async ({ update }) => {
					await update();
					loading = false;
				};
			}}
		>
			<!-- Drop Zone -->
			<div
				class="dropzone"
				class:dragover={dragOver}
				role="button"
				tabindex="0"
				ondragover={handleDragOver}
				ondragleave={handleDragLeave}
				ondrop={handleDrop}
				onclick={() => fileInput?.click()}
				onkeydown={(e) => e.key === "Enter" && fileInput?.click()}
			>
				<input
					bind:this={fileInput}
					type="file"
					name="pdf"
					accept=".pdf"
					multiple
					class="file-input"
					onchange={handleFileChange}
				/>

				{#if loading}
					<div class="dropzone-content">
						<div class="spinner"></div>
						<p class="dropzone-title">
							Processando {selectedFiles.length} arquivo{selectedFiles.length !==
							1
								? "s"
								: ""}...
						</p>
					</div>
				{:else}
					<div class="dropzone-content">
						<svg
							class="dropzone-icon"
							width="32"
							height="32"
							viewBox="0 0 24 24"
							fill="none"
							stroke="currentColor"
							stroke-width="1.5"
						>
							<path
								d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"
							/>
							<polyline points="17 8 12 3 7 8" />
							<line x1="12" y1="3" x2="12" y2="15" />
						</svg>
						<p class="dropzone-title">
							Arraste seus extratos bancários aqui
						</p>
						<p class="dropzone-subtitle">
							ou clique para selecionar • Vários arquivos
							permitidos
						</p>
						<div class="supported-banks">
							<span class="badge badge-itau">Itaú</span>
							<span class="badge badge-nubank">Nubank</span>
							<span class="badge badge-inter">Banco Inter</span>
						</div>
					</div>
				{/if}
			</div>

			<!-- Selected Files List -->
			{#if selectedFiles.length > 0 && !loading}
				<div class="file-list" style="animation: fadeIn 0.2s ease-out;">
					{#each selectedFiles as file, i}
						<div class="file-item">
							<div class="file-item-info">
								<svg
									width="16"
									height="16"
									viewBox="0 0 24 24"
									fill="none"
									stroke="currentColor"
									stroke-width="1.5"
								>
									<path
										d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"
									/>
									<polyline points="14 2 14 8 20 8" />
								</svg>
								<span class="file-name">{file.name}</span>
								<span class="file-size"
									>{formatBytes(file.size)}</span
								>
							</div>
							<button
								type="button"
								class="file-remove"
								onclick={(e) => {
									e.stopPropagation();
									removeFile(i);
								}}
								aria-label="Remover arquivo"
							>
								<svg
									width="14"
									height="14"
									viewBox="0 0 24 24"
									fill="none"
									stroke="currentColor"
									stroke-width="2"
								>
									<line x1="18" y1="6" x2="6" y2="18" />
									<line x1="6" y1="6" x2="18" y2="18" />
								</svg>
							</button>
						</div>
					{/each}
				</div>
			{/if}

			<button
				type="submit"
				class="btn btn-primary"
				disabled={loading || selectedFiles.length === 0}
			>
				{#if loading}
					<div class="btn-spinner"></div>
					Processando...
				{:else}
					<svg
						width="16"
						height="16"
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						stroke-width="2"
					>
						<polyline points="22 12 16 12 14 15 10 15 8 12 2 12" />
						<path
							d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"
						/>
					</svg>
					Extrair Transações
				{/if}
			</button>
		</form>
	</section>

	<!-- Error -->
	{#if error}
		<div class="alert alert-error" style="animation: fadeIn 0.2s ease-out;">
			<svg
				width="18"
				height="18"
				viewBox="0 0 24 24"
				fill="none"
				stroke="currentColor"
				stroke-width="2"
			>
				<circle cx="12" cy="12" r="10" />
				<line x1="15" y1="9" x2="9" y2="15" />
				<line x1="9" y1="9" x2="15" y2="15" />
			</svg>
			<p>{error}</p>
		</div>
	{/if}

	<!-- Partial Errors -->
	{#if partialErrors}
		<div
			class="alert alert-warning"
			style="animation: fadeIn 0.2s ease-out;"
		>
			<svg
				width="18"
				height="18"
				viewBox="0 0 24 24"
				fill="none"
				stroke="currentColor"
				stroke-width="2"
			>
				<path
					d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"
				/>
				<line x1="12" y1="9" x2="12" y2="13" />
				<line x1="12" y1="17" x2="12.01" y2="17" />
			</svg>
			<div>
				{#each partialErrors as err}
					<p>{err}</p>
				{/each}
			</div>
		</div>
	{/if}

	<!-- Results -->
	{#if hasResults}
		<div style="animation: slideUp 0.3s ease-out;">
			<!-- Summary Cards -->
			<div class="summary-row">
				<div class="summary-card">
					<div class="summary-icon">
						<svg
							width="18"
							height="18"
							viewBox="0 0 24 24"
							fill="none"
							stroke="currentColor"
							stroke-width="1.5"
						>
							<rect x="3" y="3" width="18" height="18" rx="0" />
							<path d="M3 9h18" />
							<path d="M9 21V9" />
						</svg>
					</div>
					<div class="summary-label">Bancos</div>
					<div class="summary-value">
						{#each banks as b}
							<span class="badge badge-{b}">{bankLabel(b)}</span>
						{/each}
					</div>
				</div>
				<div class="summary-card">
					<div class="summary-icon">
						<svg
							width="18"
							height="18"
							viewBox="0 0 24 24"
							fill="none"
							stroke="currentColor"
							stroke-width="1.5"
						>
							<line x1="8" y1="6" x2="21" y2="6" />
							<line x1="8" y1="12" x2="21" y2="12" />
							<line x1="8" y1="18" x2="21" y2="18" />
							<line x1="3" y1="6" x2="3.01" y2="6" />
							<line x1="3" y1="12" x2="3.01" y2="12" />
							<line x1="3" y1="18" x2="3.01" y2="18" />
						</svg>
					</div>
					<div class="summary-label">Transações</div>
					<div class="summary-value num">{transactions.length}</div>
				</div>
				<div class="summary-card">
					<div class="summary-icon success">
						<svg
							width="18"
							height="18"
							viewBox="0 0 24 24"
							fill="none"
							stroke="currentColor"
							stroke-width="1.5"
						>
							<line x1="12" y1="19" x2="12" y2="5" />
							<polyline points="5 12 12 5 19 12" />
						</svg>
					</div>
					<div class="summary-label">Total Entradas</div>
					<div class="summary-value num deposit">
						{formatCurrency(totalDeposits)}
					</div>
				</div>
				<div class="summary-card">
					<div class="summary-icon danger">
						<svg
							width="18"
							height="18"
							viewBox="0 0 24 24"
							fill="none"
							stroke="currentColor"
							stroke-width="1.5"
						>
							<line x1="12" y1="5" x2="12" y2="19" />
							<polyline points="19 12 12 19 5 12" />
						</svg>
					</div>
					<div class="summary-label">Total Saídas</div>
					<div class="summary-value num withdrawal">
						{formatCurrency(-totalWithdrawals)}
					</div>
				</div>
			</div>

			<!-- Actions -->
			<div class="actions-row">
				<button class="btn btn-secondary" onclick={copyToClipboard}>
					{#if copied}
						<svg
							width="14"
							height="14"
							viewBox="0 0 24 24"
							fill="none"
							stroke="currentColor"
							stroke-width="2"
						>
							<polyline points="20 6 9 17 4 12" />
						</svg>
						Copiado!
					{:else}
						<svg
							width="14"
							height="14"
							viewBox="0 0 24 24"
							fill="none"
							stroke="currentColor"
							stroke-width="1.5"
						>
							<rect x="9" y="9" width="13" height="13" rx="0" />
							<path
								d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"
							/>
						</svg>
						Copiar
					{/if}
				</button>
				<button class="btn btn-secondary" onclick={exportCSV}>
					<svg
						width="14"
						height="14"
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						stroke-width="1.5"
					>
						<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
						<polyline points="7 10 12 15 17 10" />
						<line x1="12" y1="15" x2="12" y2="3" />
					</svg>
					Exportar CSV
				</button>
			</div>

			<!-- Transaction Table -->
			<div class="table-wrapper">
				<table class="tx-table">
					<thead>
						<tr>
							<th>Data</th>
							<th class="th-right">Valor</th>
							<th>Tipo</th>
							<th>Operação</th>
							{#if banks.length > 1}
								<th>Banco</th>
							{/if}
							<th>Descrição</th>
						</tr>
					</thead>
					<tbody>
						{#each paginatedTransactions as tx, i}
							<tr
								style="animation: fadeIn {0.03 *
									Math.min(i, 15)}s ease-out;"
							>
								<td class="cell-date">{tx.date}</td>
								<td class="cell-amount {tx.operation_type}">
									{formatCurrency(tx.amount)}
								</td>
								<td>
									<span class="type-badge"
										>{tx.transaction_type}</span
									>
								</td>
								<td>
									<span
										class="operation-badge {tx.operation_type}"
									>
										{#if tx.operation_type === "deposit"}
											<svg
												width="10"
												height="10"
												viewBox="0 0 24 24"
												fill="none"
												stroke="currentColor"
												stroke-width="2.5"
												><line
													x1="12"
													y1="19"
													x2="12"
													y2="5"
												/><polyline
													points="5 12 12 5 19 12"
												/></svg
											>
											Entrada
										{:else}
											<svg
												width="10"
												height="10"
												viewBox="0 0 24 24"
												fill="none"
												stroke="currentColor"
												stroke-width="2.5"
												><line
													x1="12"
													y1="5"
													x2="12"
													y2="19"
												/><polyline
													points="19 12 12 19 5 12"
												/></svg
											>
											Saída
										{/if}
									</span>
								</td>
								{#if banks.length > 1}
									<td
										><span class="badge badge-{tx.bank}"
											>{bankLabel(tx.bank)}</span
										></td
									>
								{/if}
								<td class="cell-desc" title={tx.description}
									>{tx.description}</td
								>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>

			<!-- Pagination Controls -->
			<div class="pagination-controls">
				<div class="items-per-page">
					<label for="perPage">Itens por página:</label>
					<select id="perPage" bind:value={itemsPerPage} onchange={() => currentPage = 1}>
						<option value={10}>10</option>
						<option value={25}>25</option>
						<option value={50}>50</option>
					</select>
				</div>
				<div class="page-navigation">
					<button 
						class="btn btn-secondary btn-icon" 
						disabled={currentPage === 1}
						onclick={() => currentPage -= 1}
					>
						Anterior
					</button>
					<span class="page-info">
						Página {currentPage} de {totalPages}
					</span>
					<button 
						class="btn btn-secondary btn-icon" 
						disabled={currentPage === totalPages}
						onclick={() => currentPage += 1}
					>
						Próximo
					</button>
				</div>
			</div>
		</div>
	{/if}
</main>

<!-- ─── Footer ─── -->
<footer class="footer">
	<div class="container">
		<p>
			<svg
				width="12"
				height="12"
				viewBox="0 0 24 24"
				fill="none"
				stroke="currentColor"
				stroke-width="1.5"
				style="vertical-align: -1px;"
			>
				<rect x="3" y="11" width="18" height="11" rx="0" />
				<path d="M7 11V7a5 5 0 0 1 10 0v4" />
			</svg>
			Open Source — Seus dados nunca saem do seu computador
		</p>
	</div>
</footer>

<style>
	/* ─── Header ─── */
	.header {
		border-bottom: 1px solid var(--border);
		padding: 16px 0;
		background: var(--bg-primary);
		position: sticky;
		top: 0;
		z-index: 100;
	}

	.header-content {
		display: flex;
		align-items: center;
		justify-content: space-between;
	}

	.logo {
		display: flex;
		align-items: center;
		gap: 12px;
	}

	.logo h1 {
		font-size: 1.1rem;
		font-weight: 700;
		letter-spacing: -0.02em;
	}

	.tagline {
		font-size: 0.75rem;
		color: var(--text-muted);
	}

	.github-link {
		display: flex;
		align-items: center;
		gap: 6px;
		padding: 8px 14px;
		border: 1px solid var(--border);
		font-size: 0.8rem;
		font-weight: 500;
		color: var(--text-secondary);
		transition: all var(--transition);
	}

	.github-link:hover {
		border-color: var(--text-primary);
		color: var(--text-primary);
	}

	/* ─── Main ─── */
	.main {
		padding-top: 48px;
		padding-bottom: 80px;
		min-height: calc(100vh - 120px);
	}

	/* ─── Upload ─── */
	.upload-section {
		max-width: 640px;
		margin: 0 auto 32px;
	}

	.dropzone {
		border: 1.5px dashed var(--border);
		padding: 40px 32px;
		text-align: center;
		cursor: pointer;
		transition: all var(--transition);
		background: var(--bg-secondary);
		margin-bottom: 12px;
	}

	.dropzone:hover,
	.dropzone.dragover {
		border-color: var(--text-primary);
		background: var(--accent-dim);
	}

	.dropzone-content {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 8px;
	}

	.dropzone-icon {
		color: var(--text-muted);
		margin-bottom: 4px;
	}

	.dropzone-title {
		font-size: 0.9rem;
		font-weight: 600;
		color: var(--text-primary);
	}

	.dropzone-subtitle {
		font-size: 0.8rem;
		color: var(--text-muted);
	}

	.supported-banks {
		display: flex;
		gap: 6px;
		margin-top: 10px;
	}

	.file-input {
		display: none;
	}

	/* ─── File List ─── */
	.file-list {
		display: flex;
		flex-direction: column;
		gap: 4px;
		margin-bottom: 12px;
	}

	.file-item {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 10px 14px;
		background: var(--bg-secondary);
		border: 1px solid var(--border);
	}

	.file-item-info {
		display: flex;
		align-items: center;
		gap: 8px;
		min-width: 0;
		color: var(--text-secondary);
	}

	.file-name {
		font-size: 0.82rem;
		font-weight: 500;
		color: var(--text-primary);
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.file-size {
		font-size: 0.72rem;
		color: var(--text-muted);
		white-space: nowrap;
	}

	.file-remove {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 24px;
		height: 24px;
		border: none;
		background: none;
		cursor: pointer;
		color: var(--text-muted);
		transition: color var(--transition);
		flex-shrink: 0;
	}

	.file-remove:hover {
		color: var(--danger);
	}

	/* ─── Buttons ─── */
	.btn {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		gap: 8px;
		padding: 10px 20px;
		border: none;
		font-family: inherit;
		font-size: 0.82rem;
		font-weight: 600;
		cursor: pointer;
		transition: all var(--transition);
	}

	.btn-primary {
		width: 100%;
		background: var(--text-primary);
		color: var(--bg-primary);
	}

	.btn-primary:hover:not(:disabled) {
		background: var(--accent-hover);
	}

	.btn-primary:disabled {
		opacity: 0.25;
		cursor: not-allowed;
	}

	.btn-secondary {
		background: var(--bg-primary);
		color: var(--text-primary);
		border: 1px solid var(--border);
	}

	.btn-secondary:hover {
		border-color: var(--border-hover);
		background: var(--bg-secondary);
	}

	/* ─── Spinner ─── */
	.spinner {
		width: 28px;
		height: 28px;
		border: 2px solid var(--border);
		border-top-color: var(--text-muted);
		border-radius: 50%;
		animation: spin 0.8s linear infinite;
	}

	.btn-spinner {
		width: 14px;
		height: 14px;
		border: 2px solid rgba(255, 255, 255, 0.3);
		border-top-color: white;
		border-radius: 50%;
		animation: spin 0.8s linear infinite;
	}

	/* ─── Alerts ─── */
	.alert {
		display: flex;
		align-items: flex-start;
		gap: 10px;
		padding: 14px 16px;
		margin-bottom: 24px;
		max-width: 640px;
		margin-left: auto;
		margin-right: auto;
	}

	.alert-error {
		background: var(--danger-dim);
		border: 1px solid rgba(220, 38, 38, 0.15);
		color: var(--danger);
	}

	.alert-warning {
		background: var(--warning-dim);
		border: 1px solid rgba(217, 119, 6, 0.15);
		color: var(--warning);
	}

	.alert p {
		font-size: 0.82rem;
		line-height: 1.5;
	}

	/* ─── Summary ─── */
	.summary-row {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
		gap: 1px;
		margin-bottom: 20px;
		background: var(--border);
		border: 1px solid var(--border);
	}

	.summary-card {
		background: var(--bg-primary);
		padding: 20px;
	}

	.summary-icon {
		color: var(--text-muted);
		margin-bottom: 10px;
	}

	.summary-icon.success {
		color: var(--success);
	}

	.summary-icon.danger {
		color: var(--danger);
	}

	.summary-label {
		font-size: 0.68rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.06em;
		color: var(--text-muted);
		margin-bottom: 6px;
	}

	.summary-value {
		display: flex;
		align-items: center;
		gap: 6px;
		flex-wrap: wrap;
	}

	.summary-value.num {
		font-size: 1.3rem;
		font-weight: 700;
		font-variant-numeric: tabular-nums;
	}

	.summary-value.deposit {
		color: var(--success);
	}
	.summary-value.withdrawal {
		color: var(--danger);
	}

	/* ─── Actions ─── */
	.actions-row {
		display: flex;
		gap: 8px;
		margin-bottom: 20px;
	}

	/* ─── Pagination ─── */
	.pagination-controls {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 16px 0;
		margin-top: 10px;
		flex-wrap: wrap;
		gap: 16px;
	}

	.items-per-page {
		display: flex;
		align-items: center;
		gap: 8px;
		font-size: 0.82rem;
		color: var(--text-secondary);
	}

	.items-per-page select {
		padding: 4px 8px;
		border-radius: 4px;
		border: 1px solid var(--border);
		background-color: var(--bg-primary);
		color: var(--text-primary);
		font-size: 0.82rem;
		cursor: pointer;
	}

	.page-navigation {
		display: flex;
		align-items: center;
		gap: 12px;
	}

	.page-info {
		font-size: 0.82rem;
		color: var(--text-secondary);
		font-variant-numeric: tabular-nums;
	}

	.btn-icon {
		padding: 6px 12px;
		font-size: 0.82rem;
	}

	/* ─── Table ─── */
	.table-wrapper {
		overflow-x: auto;
		border: 1px solid var(--border);
	}

	.tx-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.82rem;
	}

	.tx-table thead {
		background: var(--bg-secondary);
	}

	.tx-table th {
		padding: 12px 16px;
		text-align: left;
		font-size: 0.68rem;
		font-weight: 700;
		text-transform: uppercase;
		letter-spacing: 0.08em;
		color: var(--text-muted);
		border-bottom: 1px solid var(--border);
	}

	.th-right {
		text-align: right !important;
	}

	.tx-table td {
		padding: 10px 16px;
		border-bottom: 1px solid var(--border);
		vertical-align: middle;
	}

	.tx-table tbody tr {
		transition: background var(--transition);
	}

	.tx-table tbody tr:hover {
		background: var(--bg-secondary);
	}

	.cell-date {
		white-space: nowrap;
		font-variant-numeric: tabular-nums;
		color: var(--text-secondary);
		font-size: 0.78rem;
	}

	.cell-desc {
		max-width: 280px;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.cell-amount {
		font-weight: 600;
		font-variant-numeric: tabular-nums;
		white-space: nowrap;
		text-align: right;
	}

	.cell-amount.deposit {
		color: var(--success);
	}
	.cell-amount.withdrawal {
		color: var(--danger);
	}

	.type-badge {
		display: inline-block;
		padding: 3px 8px;
		font-size: 0.68rem;
		font-weight: 600;
		background: var(--bg-secondary);
		color: var(--text-secondary);
		border: 1px solid var(--border);
		letter-spacing: 0.03em;
	}

	.operation-badge {
		display: inline-flex;
		align-items: center;
		gap: 4px;
		padding: 3px 8px;
		font-size: 0.68rem;
		font-weight: 600;
	}

	.operation-badge.deposit {
		background: var(--success-dim);
		color: var(--success);
	}

	.operation-badge.withdrawal {
		background: var(--danger-dim);
		color: var(--danger);
	}

	/* ─── Footer ─── */
	.footer {
		border-top: 1px solid var(--border);
		padding: 24px 0;
		text-align: center;
	}

	.footer p {
		font-size: 0.75rem;
		color: var(--text-muted);
	}

	/* ─── Responsive ─── */
	@media (max-width: 640px) {
		.header-content {
			flex-direction: column;
			gap: 12px;
		}

		.dropzone {
			padding: 28px 16px;
		}

		.summary-row {
			grid-template-columns: repeat(2, 1fr);
		}

		.actions-row {
			flex-direction: column;
		}

		.pagination-controls {
			flex-direction: column;
			align-items: stretch;
		}
		
		.page-navigation {
			justify-content: space-between;
		}

		.btn-secondary {
			width: 100%;
		}
	}
</style>
